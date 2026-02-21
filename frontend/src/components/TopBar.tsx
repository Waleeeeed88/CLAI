"use client";

import { Settings, FolderOpen, History, Plus, Zap } from "lucide-react";
import { cn } from "../lib/cn";

interface Props {
  isRunning: boolean;
  messageCount: number;
  error: string | null;
  connectionError: boolean;
  onToggleSettings: () => void;
  onToggleFiles: () => void;
  onToggleHistory: () => void;
  onNewChat: () => void;
}

export function TopBar({
  isRunning,
  messageCount,
  error,
  connectionError,
  onToggleSettings,
  onToggleFiles,
  onToggleHistory,
  onNewChat,
}: Props) {
  return (
    <header className="flex items-center justify-between border-b border-clai-border bg-clai-surface/80 backdrop-blur-sm px-4 h-12 flex-shrink-0">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <span className="font-semibold text-sm text-clai-text tracking-tight">CLAI</span>
        </div>

        <div className="hidden sm:flex items-center gap-1.5 ml-2">
          {connectionError ? (
            <span className="flex items-center gap-1.5 text-[11px] text-clai-error font-mono">
              <span className="w-1.5 h-1.5 rounded-full bg-clai-error" />
              Offline
            </span>
          ) : isRunning ? (
            <span className="flex items-center gap-1.5 text-[11px] text-clai-accent font-mono">
              <span className="w-1.5 h-1.5 rounded-full bg-clai-accent animate-pulse" />
              Running
            </span>
          ) : error ? (
            <span className="text-[11px] text-clai-error font-mono">Error</span>
          ) : messageCount > 0 ? (
            <span className="text-[11px] text-clai-muted font-mono">
              {messageCount} responses
            </span>
          ) : (
            <span className="text-[11px] text-clai-muted font-mono">Ready</span>
          )}
        </div>
      </div>

      <div className="flex items-center gap-1">
        <TopBarButton icon={History} label="History" onClick={onToggleHistory} />
        <TopBarButton icon={FolderOpen} label="Files" onClick={onToggleFiles} />
        <TopBarButton icon={Settings} label="Settings" onClick={onToggleSettings} />
        <button
          onClick={onNewChat}
          className="flex items-center gap-1.5 ml-1 rounded-lg border border-clai-border bg-clai-card px-3 py-1.5 text-[11px] font-medium text-clai-text hover:border-clai-accent/40 hover:text-clai-accent transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">New Chat</span>
        </button>
      </div>
    </header>
  );
}

function TopBarButton({
  icon: Icon,
  label,
  onClick,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      title={label}
      className={cn(
        "p-2 rounded-lg text-clai-muted hover:text-clai-text hover:bg-clai-card transition-colors",
      )}
    >
      <Icon className="w-4 h-4" />
    </button>
  );
}
