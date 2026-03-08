"use client";

import { History, Activity, Plus, Search } from "lucide-react";
import { cn } from "../lib/cn";

interface Props {
  isRunning: boolean;
  messageCount: number;
  error: string | null;
  connectionError: boolean;
  searchValue: string;
  onSearchChange: (value: string) => void;
  onOpenHistory: () => void;
  onOpenExecution: () => void;
  activeRailTab: "history" | "execution";
  onNewChat: () => void;
}

export function TopBar({
  isRunning,
  messageCount,
  error,
  connectionError,
  searchValue,
  onSearchChange,
  onOpenHistory,
  onOpenExecution,
  activeRailTab,
  onNewChat,
}: Props) {
  return (
    <header className="border-b border-white/5 px-4 py-4 lg:px-6">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-clai-muted">
            CLAI Workspace
          </p>
          <div className="mt-1 flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-semibold tracking-tight text-white">
              CLAI Console
            </h1>
            <StatusPill
              isRunning={isRunning}
              messageCount={messageCount}
              error={error}
              connectionError={connectionError}
            />
          </div>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <div className="relative min-w-0 flex-1 sm:min-w-[280px]">
            <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-clai-muted" />
            <input
              value={searchValue}
              onChange={(e) => onSearchChange(e.target.value)}
              className="w-full rounded-[18px] border border-white/8 bg-white/[0.04] py-3 pl-11 pr-4 text-sm text-clai-text placeholder:text-clai-muted/75 focus:border-white/15 focus:outline-none"
              placeholder="Search saved sessions"
            />
          </div>

          <div className="flex items-center gap-2">
            <IconButton
              icon={History}
              active={activeRailTab === "history"}
              label="History"
              onClick={onOpenHistory}
            />
            <IconButton
              icon={Activity}
              active={activeRailTab === "execution"}
              label="Execution"
              onClick={onOpenExecution}
            />
            <button
              onClick={onNewChat}
              className="flex items-center gap-2 rounded-[18px] bg-white px-4 py-3 text-sm font-semibold text-clai-bg shadow-[0_12px_28px_rgba(0,0,0,0.28)] transition hover:translate-y-[-1px] hover:bg-[#e8e8ea]"
            >
              <Plus className="h-4 w-4" />
              <span className="hidden sm:inline">New Chat</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}

function IconButton({
  icon: Icon,
  label,
  onClick,
  active,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  onClick: () => void;
  active?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      title={label}
      className={cn(
        "flex h-11 w-11 items-center justify-center rounded-[16px] border transition-colors",
        active
          ? "border-white/12 bg-white/[0.08] text-white"
          : "border-white/8 bg-white/[0.04] text-clai-muted hover:border-white/15 hover:text-clai-text",
      )}
    >
      <Icon className="h-4 w-4" />
    </button>
  );
}

function StatusPill({
  isRunning,
  messageCount,
  error,
  connectionError,
}: {
  isRunning: boolean;
  messageCount: number;
  error: string | null;
  connectionError: boolean;
}) {
  if (connectionError) {
    return (
      <span className="rounded-full border border-clai-error/25 bg-clai-error/10 px-3 py-1 text-xs font-medium text-clai-error">
        Offline
      </span>
    );
  }

  if (isRunning) {
    return (
      <span className="rounded-full border border-white/10 bg-white/[0.06] px-3 py-1 text-xs font-medium text-white">
        Live run
      </span>
    );
  }

  if (error) {
    return (
      <span className="rounded-full border border-clai-error/25 bg-clai-error/10 px-3 py-1 text-xs font-medium text-clai-error">
        Error state
      </span>
    );
  }

  return (
    <span className="rounded-full border border-white/8 bg-white/[0.04] px-3 py-1 text-xs font-medium text-clai-muted">
      {messageCount > 0 ? `${messageCount} responses` : "Ready"}
    </span>
  );
}
