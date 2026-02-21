"use client";

import { useEffect, useState } from "react";
import { startRun, cancelRun, fetchWorkflows } from "../lib/api";
import { useChatStore } from "../store/chatStore";
import { useSSE } from "../hooks/useSSE";
import { type PhaseId } from "../lib/constants";
import { TopBar } from "../components/TopBar";
import { ChatWindow } from "../components/ChatWindow";
import { ChatInput } from "../components/ChatInput";
import { FilesPanel } from "../components/FilesPanel";
import { SettingsDrawer } from "../components/SettingsDrawer";
import { ConversationHistory, type ConversationSummary } from "../components/ConversationHistory";

export default function Home() {
  const {
    messages, phases, files,
    sessionId, isRunning, error,
    setSessionId, processEvent, reset,
  } = useChatStore();

  const [connectionError, setConnectionError] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showFiles, setShowFiles] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  // For passing suggestion card selections to ChatInput
  const [pendingPrompt, setPendingPrompt] = useState<string | undefined>(undefined);
  const [pendingPhases, setPendingPhases] = useState<PhaseId[] | undefined>(undefined);

  useEffect(() => {
    fetchWorkflows()
      .then(() => setConnectionError(false))
      .catch(() => setConnectionError(true));
  }, []);

  useSSE(sessionId, processEvent);

  const handleStart = async (
    requirement: string,
    runOpts: {
      projectName: string;
      workspaceDir: string;
      useGithub: boolean;
      selectedPhases: string[];
      selectedFiles: string[];
    },
  ) => {
    reset();
    const context: Record<string, string> = {};
    if (runOpts.workspaceDir.trim()) context.workspace_dir = runOpts.workspaceDir.trim();
    try {
      const id = await startRun({
        type: "pipeline",
        requirement,
        ...(Object.keys(context).length > 0 ? { context } : {}),
        ...(runOpts.selectedFiles.length > 0 ? { selected_files: runOpts.selectedFiles } : {}),
        project_name: runOpts.projectName || "my-project",
        use_github: runOpts.useGithub ?? false,
        selected_phases: runOpts.selectedPhases,
        workspace_dir: runOpts.workspaceDir || undefined,
      });
      setSessionId(id);
      setConnectionError(false);
    } catch {
      setConnectionError(true);
    }
  };

  const handleStop = () => {
    if (sessionId) {
      cancelRun(sessionId).catch(() => {});
    }
  };

  const handleSuggestionSelect = (prompt: string, suggestionPhases: PhaseId[]) => {
    setPendingPrompt(prompt);
    setPendingPhases(suggestionPhases);
  };

  const handleNewChat = () => {
    reset();
    setPendingPrompt(undefined);
    setPendingPhases(undefined);
  };

  // Conversation history (stub — will be localStorage-backed in Phase 4.4)
  const conversations: ConversationSummary[] = [];

  return (
    <div className="flex h-full flex-col bg-clai-bg">
      <TopBar
        isRunning={isRunning}
        messageCount={messages.length}
        error={error}
        connectionError={connectionError}
        onToggleSettings={() => setShowSettings((v) => !v)}
        onToggleFiles={() => setShowFiles((v) => !v)}
        onToggleHistory={() => setShowHistory((v) => !v)}
        onNewChat={handleNewChat}
      />

      <ChatWindow
        messages={messages}
        phases={phases}
        isRunning={isRunning}
        error={error}
        onSuggestionSelect={handleSuggestionSelect}
      />

      <ChatInput
        isRunning={isRunning}
        onSend={handleStart}
        onStop={handleStop}
        initialPrompt={pendingPrompt}
        initialPhases={pendingPhases}
      />

      {/* Drawers */}
      <FilesPanel files={files} open={showFiles} onClose={() => setShowFiles(false)} />
      <SettingsDrawer open={showSettings} onClose={() => setShowSettings(false)} />
      <ConversationHistory
        open={showHistory}
        onClose={() => setShowHistory(false)}
        conversations={conversations}
        activeId={sessionId}
        onSelect={() => {}}
        onDelete={() => {}}
      />
    </div>
  );
}
