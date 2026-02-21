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

const FILE_TOOLS = new Set(["write_file", "append_file", "delete_file"]);

interface ChatStore {
  messages: ChatMessage[];
  phases: PhaseEvent[];
  files: FileEntry[];
  sessionId: string | null;
  isRunning: boolean;
  error: string | null;

  setSessionId: (id: string) => void;
  processEvent: (event: SSEEvent) => void;
  reset: () => void;
}

export const useChatStore = create<ChatStore>((set, get) => ({
  messages: [],
  phases: [],
  files: [],
  sessionId: null,
  isRunning: false,
  error: null,

  setSessionId: (id) => set({ sessionId: id, isRunning: true, error: null }),

  processEvent: (event: SSEEvent) => {
    const { messages, files } = get();

    switch (event.type) {
      case "agent_start": {
        if (!event.agent) break;
        set({
          messages: [
            ...messages,
            {
              id: uuid(),
              agent: event.agent,
              content: "",
              toolCalls: [],
              isStreaming: true,
            },
          ],
        });
        break;
      }

      case "agent_done": {
        if (!event.agent) break;
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
        set({ messages: updated });
        break;
      }

      case "tool_call": {
        if (!event.agent || !event.tool) break;
        const tc: ToolCallRecord = { tool: event.tool, args: event.args ?? {} };

        // Track file-writing tools in file panel
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
        if (!event.agent) break;
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

        // Mark the oldest "writing" file for this agent as done/error.
        // Using oldest-first (FIFO) ensures correct ordering when multiple
        // file writes are in flight for the same agent.
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
        set((s) => ({
          phases: [...s.phases, { phase: event.phase!, status: "running" }],
        }));
        break;
      }

      case "phase_done": {
        if (!event.phase) break;
        set((s) => ({
          phases: s.phases.map((p) =>
            p.phase === event.phase
              ? { ...p, status: event.status, duration: event.duration }
              : p
          ),
        }));
        break;
      }

      case "error":
        set({ error: event.message ?? "Unknown error", isRunning: false });
        break;

      case "pipeline_complete": {
        const failed = event.status === "failed";
        set({
          isRunning: false,
          ...(failed && !get().error ? { error: "Pipeline finished with failures — check agent messages above." } : {}),
        });
        break;
      }

      case "done":
      case "stage_complete":
      case "workflow_complete":
        set({ isRunning: false });
        break;
    }
  },

  reset: () =>
    set({
      messages: [],
      phases: [],
      files: [],
      sessionId: null,
      isRunning: false,
      error: null,
    }),
}));
