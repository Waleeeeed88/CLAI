"use client";

import { useEffect, useState, useCallback } from "react";
import { AnimatePresence } from "framer-motion";
import { startRun, cancelRun, fetchWorkflows } from "../lib/api";
import { useChatStore } from "../store/chatStore";
import { useSSE } from "../hooks/useSSE";
import { type PhaseId } from "../lib/constants";
import { listConversations, deleteConversation, saveUserConfig } from "../lib/storage";
import type { ConversationSummary } from "../lib/storage";
import { TopBar } from "../components/TopBar";
import { ChatWindow } from "../components/ChatWindow";
import { ChatInput } from "../components/ChatInput";
import { ExecutionPanel } from "../components/ExecutionPanel";
import { SettingsDrawer } from "../components/SettingsDrawer";
import { ConversationHistory } from "../components/ConversationHistory";
import { Sidebar } from "../components/Sidebar";

export default function Home() {
  const {
    messages, phases, files, agentStatuses,
    sessionId, isRunning, error, startedAt,
    setSessionId, processEvent, reset, loadSession,
  } = useChatStore();

  const [connectionError, setConnectionError] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  // For passing suggestion card selections to ChatInput
  const [pendingPrompt, setPendingPrompt] = useState<string | undefined>(undefined);
  const [pendingPhases, setPendingPhases] = useState<PhaseId[] | undefined>(undefined);

  // Conversation list from localStorage
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);

  const refreshConversations = useCallback(() => {
    setConversations(listConversations());
  }, []);

  useEffect(() => {
    refreshConversations();
  }, [refreshConversations]);

  // Refresh conversation list when a session completes
  useEffect(() => {
    if (!isRunning && messages.length > 0) {
      refreshConversations();
    }
  }, [isRunning, messages.length, refreshConversations]);

  const hasContent = messages.length > 0 || isRunning;

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
    saveUserConfig({
      lastWorkspace: runOpts.workspaceDir,
      lastProjectName: runOpts.projectName,
    });
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
    refreshConversations();
  };

  const handleSelectConversation = (id: string) => {
    loadSession(id);
    setShowHistory(false);
  };

  const handleDeleteConversation = (id: string) => {
    deleteConversation(id);
    refreshConversations();
  };

  return (
    <div className="flex h-full bg-clai-bg text-clai-text">
      <Sidebar
        onToggleHistory={() => setShowHistory((v) => !v)}
        onToggleSettings={() => setShowSettings((v) => !v)}
        onNewChat={handleNewChat}
        hasContent={hasContent}
      />

      <main className="flex-1 flex flex-col min-w-0">
        <TopBar
          isRunning={isRunning}
          messageCount={messages.length}
          error={error}
          connectionError={connectionError}
          onNewChat={handleNewChat}
        />
        <div className="flex-1 flex min-h-0">
          <div className="flex-1 flex flex-col min-w-0">
            <ChatWindow
              messages={messages}
              phases={phases}
              files={files}
              isRunning={isRunning}
              error={error}
              startedAt={startedAt}
              onSuggestionSelect={handleSuggestionSelect}
              recentConversations={conversations.slice(0, 5)}
              onSelectConversation={handleSelectConversation}
            />
            <ChatInput
              isRunning={isRunning}
              onSend={handleStart}
              onStop={handleStop}
              initialPrompt={pendingPrompt}
              initialPhases={pendingPhases}
            />
          </div>

          {/* Inline execution panel — visible when there's content */}
          <AnimatePresence>
            {hasContent && (
              <ExecutionPanel
                agentStatuses={agentStatuses}
                phases={phases}
                files={files}
                isRunning={isRunning}
                startedAt={startedAt}
              />
            )}
          </AnimatePresence>
        </div>
      </main>

      {/* Drawers */}
      <SettingsDrawer open={showSettings} onClose={() => setShowSettings(false)} />
      <ConversationHistory
        open={showHistory}
        onClose={() => setShowHistory(false)}
        conversations={conversations}
        activeId={sessionId}
        onSelect={handleSelectConversation}
        onDelete={handleDeleteConversation}
      />
    </div>
  );
}
