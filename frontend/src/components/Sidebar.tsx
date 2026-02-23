import React from "react";
import { History, Settings, Zap, Plus } from "lucide-react";
import { cn } from "../lib/cn";

interface SidebarProps {
  onToggleHistory: () => void;
  onToggleSettings: () => void;
  onNewChat: () => void;
  hasContent: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  onToggleHistory,
  onToggleSettings,
  onNewChat,
  hasContent,
}) => {
  return (
    <aside className="z-10 flex w-16 flex-col justify-between border-r border-clai-border/80 bg-clai-surface/70 p-3 backdrop-blur-xl md:w-56 md:p-4">
      <div>
        <div className="mb-7 flex items-center gap-2 rounded-xl border border-cyan-300/20 bg-cyan-500/10 p-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-cyan-400 to-emerald-400">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <div className="hidden md:block">
            <p className="text-xs font-semibold tracking-[0.14em] text-white">CLAI</p>
            <p className="text-[10px] uppercase tracking-[0.16em] text-cyan-200/80">Command</p>
          </div>
        </div>

        <nav className="flex flex-col gap-2">
          <SidebarButton
            icon={Plus}
            label="New Chat"
            onClick={onNewChat}
            accent
          />
          <SidebarButton
            icon={History}
            label="History"
            onClick={onToggleHistory}
          />
        </nav>
      </div>
      <div>
        <SidebarButton
          icon={Settings}
          label="Settings"
          onClick={onToggleSettings}
        />
      </div>
    </aside>
  );
};

function SidebarButton({
  icon: Icon,
  label,
  onClick,
  isActive,
  accent,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  onClick: () => void;
  isActive?: boolean;
  accent?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "group flex w-full items-center gap-3 rounded-lg p-2 transition-colors md:p-2.5",
        accent
          ? "bg-clai-accent/10 text-clai-accent border border-clai-accent/20 hover:bg-clai-accent/20"
          : "text-clai-muted hover:bg-clai-card/80 hover:text-clai-text",
        isActive && "bg-clai-card text-clai-text shadow-[inset_0_0_0_1px_rgba(56,189,248,0.25)]"
      )}
    >
      <Icon className="h-4 w-4 shrink-0" />
      <span className="hidden text-sm font-medium md:inline">{label}</span>
    </button>
  );
}

export default Sidebar;
