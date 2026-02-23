"use client";

import { Plus } from "lucide-react";

interface Props {
  isRunning: boolean;
  messageCount: number;
  error: string | null;
  connectionError: boolean;
  onNewChat: () => void;
}

export function TopBar({
  isRunning,
  messageCount,
  error,
  connectionError,
  onNewChat,
}: Props) {
  return (
    <header className="flex items-center justify-between border-b border-clai-border bg-clai-surface/80 backdrop-blur-sm px-4 h-12 flex-shrink-0">
      <div className="flex items-center gap-3">
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
