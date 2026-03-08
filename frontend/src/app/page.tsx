"use client";

import { useEffect, useMemo, useState, useCallback } from "react";
import { startRun, cancelRun, fetchWorkflows } from "../lib/api";
import { useChatStore } from "../store/chatStore";
import { useSSE } from "../hooks/useSSE";
import { type PhaseId } from "../lib/constants";
import { listConversations, deleteConversation, saveUserConfig } from "../lib/storage";
import type { ConversationSummary } from "../lib/storage";
import { TopBar } from "../components/TopBar";
import { ChatWindow } from "../components/ChatWindow";
import { ChatInput } from "../components/ChatInput";
import { SettingsDrawer } from "../components/SettingsDrawer";
import { RightRail } from "../components/RightRail";
import { Sidebar } from "../components/Sidebar";

type RightRailTab = "history" | "execution";

export default function Home() {
  const {
    messages, phases, files, agentStatuses,
    sessionId, isRunning, error, startedAt,
    setSessionId, processEvent, reset, loadSession,
  } = useChatStore();

  const [connectionError, setConnectionError] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showMobileRail, setShowMobileRail] = useState(false);
  const [activeRailTab, setActiveRailTab] = useState<RightRailTab>("history");
  const [historyQuery, setHistoryQuery] = useState("");

  const [pendingPrompt, setPendingPrompt] = useState<string | undefined>(undefined);
  const [pendingPhases, setPendingPhases] = useState<PhaseId[] | undefined>(undefined);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);

  const refreshConversations = useCallback(() => {
    setConversations(listConversations());
  }, []);

  useEffect(() => {
    refreshConversations();
  }, [refreshConversations]);

  useEffect(() => {
    if (!isRunning && messages.length > 0) {
      refreshConversations();
    }
  }, [isRunning, messages.length, refreshConversations]);

  useEffect(() => {
    fetchWorkflows()
      .then(() => setConnectionError(false))
      .catch(() => setConnectionError(true));
  }, []);

  useSSE(sessionId, processEvent);

  const filteredConversations = useMemo(() => {
    const q = historyQuery.trim().toLowerCase();
    if (!q) return conversations;
    return conversations.filter((conv) => conv.title.toLowerCase().includes(q));
  }, [conversations, historyQuery]);

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
    setActiveRailTab("execution");
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
    setActiveRailTab("history");
    setHistoryQuery("");
    refreshConversations();
  };

  const handleSelectConversation = (id: string) => {
    loadSession(id);
    setShowMobileRail(false);
    setActiveRailTab("history");
  };

  const handleDeleteConversation = (id: string) => {
    deleteConversation(id);
    refreshConversations();
  };

  const openRail = (tab: RightRailTab) => {
    setActiveRailTab(tab);
    setShowMobileRail(true);
  };

  return (
    <div className="min-h-screen bg-transparent">
      <div className="app-shell glass-line flex h-screen w-screen overflow-hidden">
        <Sidebar
          onOpenHistory={() => openRail("history")}
          onToggleSettings={() => setShowSettings((v) => !v)}
          onNewChat={handleNewChat}
          isRunning={isRunning}
        />

        <main className="flex min-w-0 flex-1 flex-col">
          <TopBar
            isRunning={isRunning}
            messageCount={messages.length}
            error={error}
            connectionError={connectionError}
            searchValue={historyQuery}
            onSearchChange={setHistoryQuery}
            onOpenHistory={() => openRail("history")}
            onOpenExecution={() => openRail("execution")}
            activeRailTab={activeRailTab}
            onNewChat={handleNewChat}
          />

          <div className="flex min-h-0 flex-1">
            <div className="flex min-w-0 flex-1 flex-col">
              <ChatWindow
                messages={messages}
                phases={phases}
                files={files}
                isRunning={isRunning}
                error={error}
                startedAt={startedAt}
                onSuggestionSelect={handleSuggestionSelect}
                recentConversations={filteredConversations.slice(0, 5)}
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

            <RightRail
              activeTab={activeRailTab}
              onTabChange={setActiveRailTab}
              mobileOpen={showMobileRail}
              onCloseMobile={() => setShowMobileRail(false)}
              searchValue={historyQuery}
              onSearchChange={setHistoryQuery}
              conversations={filteredConversations}
              activeId={sessionId}
              onSelectConversation={handleSelectConversation}
              onDeleteConversation={handleDeleteConversation}
              agentStatuses={agentStatuses}
              phases={phases}
              files={files}
              isRunning={isRunning}
              startedAt={startedAt}
            />
          </div>
        </main>
      </div>

      <SettingsDrawer open={showSettings} onClose={() => setShowSettings(false)} />
    </div>
  );
}
