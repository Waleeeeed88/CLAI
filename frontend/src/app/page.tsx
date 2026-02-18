"use client";
import { useCallback, useEffect, useState } from "react";
import { startRun, fetchWorkflows } from "../lib/api";
import { useChatStore } from "../store/chatStore";
import { useSSE } from "../hooks/useSSE";
import { Sidebar } from "../components/Sidebar";
import { ChatWindow } from "../components/ChatWindow";
import { FilesPanel } from "../components/FilesPanel";

export default function Home() {
  const {
    messages, phases, files,
    sessionId, isRunning, error,
    setSessionId, processEvent, reset,
  } = useChatStore();

  const [connectionError, setConnectionError] = useState(false);

  useEffect(() => {
    fetchWorkflows()
      .then(() => setConnectionError(false))
      .catch(() => setConnectionError(true));
  }, []);

  const handleEvent = useCallback(processEvent, [processEvent]);
  useSSE(sessionId, handleEvent);

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

  return (
    <div className="flex h-full flex-col lg:flex-row">
      <Sidebar onStart={handleStart} isRunning={isRunning} onReset={reset} connectionError={connectionError} />

      <div className="flex-1 flex flex-col min-w-0 min-h-0">
        <div className="border-b border-slate-800 px-6 py-2.5 flex items-center h-10 bg-slate-900/50">
          {isRunning ? (
            <span className="text-[11px] text-cyan-300 font-mono flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-300 animate-pulse" />
              Running...
            </span>
          ) : error ? (
            <span className="text-[11px] text-red-400 font-mono">Error</span>
          ) : (
            <span className="text-[11px] text-slate-400 font-mono">
              {messages.length > 0 ? `${messages.length} responses` : "Ready"}
            </span>
          )}
        </div>

        <ChatWindow messages={messages} phases={phases} isRunning={isRunning} error={error} />
      </div>

      <div className="hidden xl:block">
        <FilesPanel files={files} />
      </div>
    </div>
  );
}
