import React from "react";
import { History, PanelLeft, Settings, Plus, Sparkles } from "lucide-react";
import { cn } from "../lib/cn";

interface SidebarProps {
  onOpenHistory: () => void;
  onToggleSettings: () => void;
  onNewChat: () => void;
  isRunning: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  onOpenHistory,
  onToggleSettings,
  onNewChat,
  isRunning,
}) => {
  return (
    <aside className="panel-shell glass-line flex w-[86px] flex-col justify-between border-r border-white/6 bg-clai-shell/95 px-3 py-4 sm:w-[92px] lg:w-[252px] lg:px-5">
      <div>
        <div className="rounded-[26px] border border-white/8 bg-white/[0.02] p-3">
          <div className="flex items-center gap-3">
            <span className="flex h-11 w-11 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.06] text-white">
              <Sparkles className="h-5 w-5" />
            </span>
            <div className="hidden lg:block">
              <p className="text-2xl font-extrabold tracking-tight text-white">CLAI</p>
              <p className="text-[11px] uppercase tracking-[0.18em] text-clai-muted">AI Team Console</p>
            </div>
          </div>
        </div>

        <div className="mt-4 rounded-[22px] border border-white/6 bg-white/[0.03] p-2">
          <SidebarButton icon={PanelLeft} label="Workspace" active />
          <SidebarButton icon={History} label="History" onClick={onOpenHistory} />
          <SidebarButton icon={Settings} label="Settings" onClick={onToggleSettings} />
        </div>
      </div>

      <div className="space-y-3">
        <div className="rounded-[24px] border border-white/8 bg-white/[0.03] p-3">
          <div className="hidden lg:block">
            <p className="text-sm font-semibold text-white">Workspace status</p>
            <p className="mt-1 text-xs leading-relaxed text-clai-muted">
              {isRunning ? "Pipeline run is live. Open Execution for details." : "Ready for a new build, review, or planning run."}
            </p>
          </div>
          <div className="mt-3 flex items-center justify-between lg:mt-4">
            <span className={cn(
              "rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.18em]",
              isRunning ? "bg-white/[0.08] text-white" : "bg-white/[0.05] text-clai-muted",
            )}>
              {isRunning ? "Running" : "Ready"}
            </span>
            <button
              onClick={onNewChat}
              className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white text-clai-bg shadow-[0_12px_28px_rgba(0,0,0,0.32)] transition hover:translate-y-[-1px] hover:bg-[#e8e8ea] lg:hidden"
              title="New chat"
            >
              <Plus className="h-4 w-4" />
            </button>
          </div>
          <button
            onClick={onNewChat}
            className="mt-4 hidden w-full items-center justify-center gap-2 rounded-2xl bg-white px-4 py-3 text-sm font-semibold text-clai-bg shadow-[0_12px_28px_rgba(0,0,0,0.32)] transition hover:translate-y-[-1px] hover:bg-[#e8e8ea] lg:flex"
          >
            <Plus className="h-4 w-4" />
            New Chat
          </button>
        </div>
      </div>
    </aside>
  );
};

function SidebarButton({
  icon: Icon,
  label,
  onClick,
  active,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  onClick?: () => void;
  active?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex w-full items-center gap-3 rounded-[18px] px-3 py-3 text-left transition-all",
        active
          ? "bg-white/[0.08] text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]"
          : "text-clai-muted hover:bg-white/[0.05] hover:text-clai-text",
      )}
    >
      <Icon className="h-4 w-4 shrink-0" />
      <span className="hidden text-sm font-medium lg:inline">{label}</span>
    </button>
  );
}

export default Sidebar;
