"use client";

import { create } from "zustand";
import { v4 as uuid } from "uuid";
import {
  ChatMessage,
  FileEntry,
  PhaseEvent,
  SSEEvent,
  ToolCallRecord,
} from "../lib/types";
import { AGENTS, type AgentRole } from "../lib/constants";
import { saveConversation, loadConversation } from "../lib/storage";

const FILE_TOOLS = new Set(["write_file", "append_file", "delete_file"]);

type AgentStatus = "idle" | "thinking" | "using_tool";
type Agent = AgentRole;

interface ChatStore {
  messages: ChatMessage[];
  phases: PhaseEvent[];
  files: FileEntry[];
  agentStatuses: Record<Agent, AgentStatus>;
  sessionId: string | null;
  isRunning: boolean;
  error: string | null;
  startedAt: number | null;

  setSessionId: (id: string) => void;
  processEvent: (event: SSEEvent) => void;
  reset: () => void;
  loadSession: (id: string) => boolean;
}

const initialAgentStatuses = Object.fromEntries(
  (Object.keys(AGENTS) as Agent[]).map((role) => [role, "idle"]),
) as Record<Agent, AgentStatus>;

const isAgentRole = (value: string | undefined): value is Agent =>
  Boolean(value && Object.prototype.hasOwnProperty.call(AGENTS, value));

// Debounced save — avoids hammering localStorage on every SSE event
let saveTimer: ReturnType<typeof setTimeout> | null = null;
function debouncedSave(id: string, messages: ChatMessage[], phases: PhaseEvent[], files: FileEntry[]) {
  if (saveTimer) clearTimeout(saveTimer);
  saveTimer = setTimeout(() => {
    saveConversation(id, messages, phases, files);
  }, 2000);
}

export const useChatStore = create<ChatStore>((set, get) => ({
  messages: [],
  phases: [],
  files: [],
  agentStatuses: initialAgentStatuses,
  sessionId: null,
  isRunning: false,
  error: null,
  startedAt: null,

  setSessionId: (id) => set({ sessionId: id, isRunning: true, error: null, startedAt: Date.now() }),

  loadSession: (id: string) => {
    const data = loadConversation(id);
    if (!data) return false;
    set({
      messages: data.messages,
      phases: data.phases,
      files: data.files,
      agentStatuses: initialAgentStatuses,
      sessionId: id,
      isRunning: false,
      error: null,
      startedAt: null,
    });
    return true;
  },

  processEvent: (event: SSEEvent) => {
    const { messages, files, agentStatuses, sessionId } = get();

    switch (event.type) {
      case "agent_start": {
        if (!isAgentRole(event.agent)) break;
        const newMessages = [
          ...messages,
          {
            id: uuid(),
            agent: event.agent,
            content: "",
            toolCalls: [],
            isStreaming: true,
          },
        ];
        set({
          agentStatuses: { ...agentStatuses, [event.agent]: "thinking" },
          messages: newMessages,
        });
        if (sessionId) debouncedSave(sessionId, newMessages, get().phases, files);
        break;
      }

      case "agent_done": {
        if (!isAgentRole(event.agent)) break;
        const updated = [...messages];
        for (let i = updated.length - 1; i >= 0; i--) {
          if (updated[i].agent === event.agent && updated[i].isStreaming) {
            updated[i] = {
              ...updated[i],
              content: event.content ?? "",
              tokens: event.tokens,
              model: event.model,
              isStreaming: false,
            };
            break;
          }
        }
        set({
          messages: updated,
          agentStatuses: { ...agentStatuses, [event.agent]: "idle" },
        });
        if (sessionId) debouncedSave(sessionId, updated, get().phases, files);
        break;
      }

      case "tool_call": {
        if (!isAgentRole(event.agent) || !event.tool) break;
        set({ agentStatuses: { ...agentStatuses, [event.agent]: "using_tool" } });

        const tc: ToolCallRecord = { tool: event.tool, args: event.args ?? {} };

        const isFileTool = FILE_TOOLS.has(event.tool);
        const filePath = event.args?.file_path ?? event.args?.path;
        let newFiles = files;
        if (isFileTool && filePath) {
          newFiles = [
            ...files,
            {
              id: uuid(),
              path: filePath,
              agent: event.agent,
              tool: event.tool as FileEntry["tool"],
              status: "writing" as const,
              timestamp: Date.now(),
            },
          ];
        }

        const updatedMsgs = [...messages];
        for (let i = updatedMsgs.length - 1; i >= 0; i--) {
          if (updatedMsgs[i].agent === event.agent && updatedMsgs[i].isStreaming) {
            updatedMsgs[i] = {
              ...updatedMsgs[i],
              toolCalls: [...updatedMsgs[i].toolCalls, tc],
            };
            break;
          }
        }
        set({ messages: updatedMsgs, files: newFiles });
        break;
      }

      case "tool_result": {
        if (!isAgentRole(event.agent)) break;
        set({ agentStatuses: { ...agentStatuses, [event.agent]: "thinking" } });
        const updatedMsgs = [...messages];
        for (let i = updatedMsgs.length - 1; i >= 0; i--) {
          if (updatedMsgs[i].agent === event.agent && updatedMsgs[i].isStreaming) {
            const toolCalls = [...updatedMsgs[i].toolCalls];
            if (toolCalls.length > 0) {
              toolCalls[toolCalls.length - 1] = {
                ...toolCalls[toolCalls.length - 1],
                result: event.preview,
                success: event.success,
              };
            }
            updatedMsgs[i] = { ...updatedMsgs[i], toolCalls };
            break;
          }
        }

        const isFileResult = event.tool ? FILE_TOOLS.has(event.tool) : false;
        const updatedFiles = [...files];
        if (isFileResult) {
          for (let i = 0; i < updatedFiles.length; i++) {
            if (
              updatedFiles[i].agent === event.agent &&
              updatedFiles[i].status === "writing"
            ) {
              updatedFiles[i] = {
                ...updatedFiles[i],
                status: event.success ? "done" : "error",
              };
              break;
            }
          }
        }
        set({ messages: updatedMsgs, files: updatedFiles });
        break;
      }

      case "phase_start": {
        if (!event.phase) break;
        const phase = event.phase;
        set((s) => ({
          phases: [...s.phases, { phase, status: "running" }],
        }));
        break;
      }

      case "phase_done": {
        if (!event.phase) break;
        const phase = event.phase;
        set((s) => ({
          phases: s.phases.map((p) =>
            p.phase === phase
              ? { ...p, status: event.status, duration: event.duration }
              : p,
          ),
        }));
        break;
      }

      case "error":
        set({
          error: event.message ?? "Unknown error",
          isRunning: false,
          agentStatuses: initialAgentStatuses,
        });
        // Final save on error
        if (sessionId) {
          const s = get();
          saveConversation(sessionId, s.messages, s.phases, s.files);
        }
        break;

      case "pipeline_complete": {
        const failed = event.status === "failed";
        set({
          isRunning: false,
          agentStatuses: initialAgentStatuses,
          ...(failed && !get().error
            ? { error: "Pipeline finished with failures - check agent messages above." }
            : {}),
        });
        // Final save on completion
        if (sessionId) {
          const s = get();
          saveConversation(sessionId, s.messages, s.phases, s.files);
        }
        break;
      }

      case "done":
      case "stage_complete":
      case "workflow_complete":
        set({ isRunning: false, agentStatuses: initialAgentStatuses });
        if (sessionId) {
          const s = get();
          saveConversation(sessionId, s.messages, s.phases, s.files);
        }
        break;
    }
  },

  reset: () => {
    // Save current session before clearing
    const { sessionId, messages, phases, files } = get();
    if (sessionId && messages.length > 0) {
      saveConversation(sessionId, messages, phases, files);
    }
    if (saveTimer) clearTimeout(saveTimer);
    set({
      messages: [],
      phases: [],
      files: [],
      agentStatuses: initialAgentStatuses,
      sessionId: null,
      isRunning: false,
      error: null,
      startedAt: null,
    });
  },
}));
