"use client";

import { useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search, X, History, Activity, Clock3, Trash2, FileCode2,
  Crown, Code2, Braces, Sparkles, TestTube2, FileSearch, Eye,
  CircleDot, CheckCircle2,
} from "lucide-react";
import { cn } from "../lib/cn";
import { AGENTS, type AgentRole } from "../lib/constants";
import type { ConversationSummary } from "../lib/storage";
import type { FileEntry, PhaseEvent } from "../lib/types";

type AgentStatus = "idle" | "thinking" | "using_tool";
type RailTab = "history" | "execution";

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  Crown,
  Code2,
  Braces,
  Sparkles,
  TestTube2,
  FileSearch,
  Eye,
};

interface Props {
  activeTab: RailTab;
  onTabChange: (tab: RailTab) => void;
  mobileOpen: boolean;
  onCloseMobile: () => void;
  searchValue: string;
  onSearchChange: (value: string) => void;
  conversations: ConversationSummary[];
  activeId: string | null;
  onSelectConversation: (id: string) => void;
  onDeleteConversation: (id: string) => void;
  agentStatuses: Record<AgentRole, AgentStatus>;
  phases: PhaseEvent[];
  files: FileEntry[];
  isRunning: boolean;
  startedAt: number | null;
}

function timeAgo(timestamp: number): string {
  const diff = Date.now() - timestamp;
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function formatElapsed(startedAt: number | null) {
  if (!startedAt) return "--";
  const elapsed = Math.floor((Date.now() - startedAt) / 1000);
  const mins = Math.floor(elapsed / 60);
  const secs = elapsed % 60;
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

function RailInner({
  activeTab,
  onTabChange,
  searchValue,
  onSearchChange,
  conversations,
  activeId,
  onSelectConversation,
  onDeleteConversation,
  agentStatuses,
  phases,
  files,
  isRunning,
  startedAt,
}: Omit<Props, "mobileOpen" | "onCloseMobile">) {
  const activeAgents = Object.values(agentStatuses).filter((status) => status !== "idle").length;
  const doneFiles = files.filter((file) => file.status === "done").length;
  const recentFiles = useMemo(
    () => [...files].sort((a, b) => b.timestamp - a.timestamp).slice(0, 8),
    [files],
  );

  return (
    <div className="panel-shell glass-line flex h-full flex-col border-l border-white/6 bg-clai-shell/95">
      <div className="flex items-center justify-between border-b border-white/6 px-4 py-4">
        <div>
          <p className="text-xl font-semibold tracking-tight text-clai-text">
            {activeTab === "history" ? "History" : "Execution"}
          </p>
          <p className="text-xs text-clai-muted">
            {activeTab === "history"
              ? `${conversations.length} saved conversation${conversations.length === 1 ? "" : "s"}`
              : isRunning
              ? "Live pipeline activity"
              : "Latest pipeline state"}
          </p>
        </div>
        <div className="rounded-full border border-white/10 bg-white/[0.05] px-3 py-1 text-xs font-medium text-clai-muted">
          {activeTab === "history" ? `${conversations.length}` : `${activeAgents}/${Object.keys(AGENTS).length}`}
        </div>
      </div>

      <div className="border-b border-white/6 px-4 py-3">
        <div className="grid grid-cols-2 gap-2 rounded-2xl bg-white/[0.03] p-1">
          {[
            { id: "history" as const, label: "History", icon: History },
            { id: "execution" as const, label: "Execution", icon: Activity },
          ].map(({ id, label, icon: Icon }) => {
            const active = activeTab === id;
            return (
              <button
                key={id}
                onClick={() => onTabChange(id)}
                className={cn(
                  "flex items-center justify-center gap-2 rounded-2xl px-3 py-2 text-sm transition-all",
                  active
                    ? "bg-white/[0.08] text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]"
                    : "text-clai-muted hover:bg-white/[0.05] hover:text-clai-text",
                )}
              >
                <Icon className="h-4 w-4" />
                {label}
              </button>
            );
          })}
        </div>

        {activeTab === "history" && (
          <div className="relative mt-3">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-clai-muted" />
            <input
              value={searchValue}
              onChange={(e) => onSearchChange(e.target.value)}
              className="w-full rounded-2xl border border-white/8 bg-white/[0.04] py-2.5 pl-10 pr-3 text-sm text-clai-text placeholder:text-clai-muted/70 focus:border-white/15 focus:outline-none"
              placeholder="Search saved sessions"
            />
          </div>
        )}
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto p-4">
        {activeTab === "history" ? (
          <div className="space-y-3">
            {conversations.length === 0 ? (
              <div className="rounded-[24px] border border-dashed border-white/10 bg-white/[0.03] px-5 py-8 text-center text-sm text-clai-muted">
                No saved sessions match this search.
              </div>
            ) : (
              conversations.map((conv) => {
                const active = conv.id === activeId;
                return (
                  <button
                    key={conv.id}
                    onClick={() => onSelectConversation(conv.id)}
                    className={cn(
                      "group block w-full rounded-[22px] border px-4 py-4 text-left transition-all",
                      active
                        ? "border-white/12 bg-white/[0.07] shadow-[0_10px_25px_rgba(0,0,0,0.18)]"
                        : "border-white/6 bg-white/[0.03] hover:border-white/15 hover:bg-white/[0.05]",
                    )}
                  >
                    <div className="flex items-start gap-3">
                      <span className="mt-0.5 flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-2xl bg-white/[0.06] text-clai-text">
                        <History className="h-4 w-4" />
                      </span>
                      <div className="min-w-0 flex-1">
                        <div className="truncate text-[15px] font-medium text-clai-text">
                          {conv.title}
                        </div>
                        <div className="mt-2 flex items-center gap-2 text-[11px] text-clai-muted">
                          <span>{conv.messageCount} messages</span>
                          <span className="text-white/10">/</span>
                          <Clock3 className="h-3 w-3" />
                          <span>{timeAgo(conv.updatedAt)}</span>
                        </div>
                      </div>
                      <span
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteConversation(conv.id);
                        }}
                        className="rounded-xl border border-transparent p-2 text-clai-muted opacity-0 transition-all group-hover:opacity-100 hover:border-white/10 hover:bg-white/5 hover:text-clai-error"
                      >
                        <Trash2 className="h-4 w-4" />
                      </span>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        ) : (
          <div className="space-y-4">
            <div className="rounded-[24px] border border-white/8 bg-white/[0.04] p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold text-clai-text">
                    {isRunning ? "Pipeline in progress" : "Pipeline idle"}
                  </p>
                  <p className="mt-1 text-xs text-clai-muted">
                    Monitor live agent work, phase changes, and file output.
                  </p>
                </div>
                <div className={cn(
                  "rounded-2xl px-3 py-1.5 text-xs font-medium",
                  isRunning ? "bg-white/[0.08] text-white" : "bg-white/[0.05] text-clai-muted",
                )}>
                  {isRunning ? "Running" : "Ready"}
                </div>
              </div>
              <div className="mt-4 grid grid-cols-3 gap-2">
                <MetricCard label="Elapsed" value={formatElapsed(startedAt)} />
                <MetricCard label="Agents" value={`${activeAgents}/${Object.keys(AGENTS).length}`} />
                <MetricCard label="Files" value={`${doneFiles}/${files.length}`} />
              </div>
            </div>

            <section>
              <SectionTitle>Team activity</SectionTitle>
              <div className="space-y-2">
                {(Object.entries(AGENTS) as [AgentRole, (typeof AGENTS)[AgentRole]][]).map(([role, meta]) => {
                  const status = agentStatuses[role];
                  const Icon = ICON_MAP[meta.icon] ?? Code2;
                  const active = status !== "idle";
                  return (
                    <div
                      key={role}
                      className={cn(
                        "flex items-center gap-3 rounded-[22px] border px-3 py-3",
                        active ? "border-white/10 bg-white/[0.05]" : "border-white/5 bg-white/[0.025]",
                      )}
                    >
                      <span
                        className="flex h-10 w-10 items-center justify-center rounded-2xl"
                        style={{ backgroundColor: `${meta.color}18`, color: meta.color }}
                      >
                        <Icon className="h-4 w-4" />
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-clai-text">{meta.label}</p>
                        <p className="text-xs text-clai-muted">
                          {status === "using_tool" ? "Using tools" : status === "thinking" ? "Working" : "Idle"}
                        </p>
                      </div>
                      <span className={cn(
                        "h-2.5 w-2.5 rounded-full",
                        status === "idle" && "bg-white/20",
                        status === "thinking" && "bg-white animate-pulse",
                        status === "using_tool" && "bg-clai-text animate-pulse",
                      )} />
                    </div>
                  );
                })}
              </div>
            </section>

            {phases.length > 0 && (
              <section>
                <SectionTitle>Phase progress</SectionTitle>
                <div className="space-y-2">
                  {phases.map((phase, index) => {
                    const status = (phase.status ?? "running").toLowerCase();
                    return (
                      <div
                        key={`${phase.phase}-${index}`}
                        className="rounded-[22px] border border-white/8 bg-white/[0.04] px-4 py-3"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            {status === "completed" || status === "done" ? (
                              <CheckCircle2 className="h-4 w-4 text-clai-text" />
                            ) : (
                              <CircleDot className={cn("h-4 w-4", status === "failed" ? "text-clai-error" : "text-clai-text")} />
                            )}
                            <span className="text-sm font-medium capitalize text-clai-text">
                              {phase.phase.replace(/_/g, " ")}
                            </span>
                          </div>
                          <span className="text-xs font-mono text-clai-muted">
                            {phase.duration != null ? `${phase.duration.toFixed(1)}s` : status}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </section>
            )}

            {recentFiles.length > 0 && (
              <section>
                <SectionTitle>Recent files</SectionTitle>
                <div className="space-y-2">
                  {recentFiles.map((file) => {
                    const meta = AGENTS[file.agent as AgentRole];
                    return (
                      <div
                        key={file.id}
                        className="flex items-center gap-3 rounded-[22px] border border-white/8 bg-white/[0.04] px-4 py-3"
                      >
                        <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white/5 text-clai-muted">
                          <FileCode2 className="h-4 w-4" />
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="truncate font-mono text-xs text-clai-text">
                            {file.path}
                          </p>
                          <p className="mt-1 text-[11px] text-clai-muted">
                            {meta?.label ?? file.agent}
                          </p>
                        </div>
                        <span className={cn(
                          "rounded-full px-2 py-1 text-[10px] font-medium",
                          file.status === "done" && "bg-white/[0.08] text-white",
                          file.status === "writing" && "bg-white/[0.06] text-clai-text",
                          file.status === "error" && "bg-clai-error/15 text-clai-error",
                        )}>
                          {file.status}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </section>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[18px] border border-white/8 bg-black/15 px-3 py-2.5 text-center">
      <p className="text-[10px] uppercase tracking-[0.18em] text-clai-muted">{label}</p>
      <p className="mt-1 text-sm font-semibold text-clai-text">{value}</p>
    </div>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="mb-2 px-1 text-[10px] font-semibold uppercase tracking-[0.22em] text-clai-muted">
      {children}
    </h3>
  );
}

export function RightRail(props: Props) {
  const innerProps = {
    activeTab: props.activeTab,
    onTabChange: props.onTabChange,
    searchValue: props.searchValue,
    onSearchChange: props.onSearchChange,
    conversations: props.conversations,
    activeId: props.activeId,
    onSelectConversation: props.onSelectConversation,
    onDeleteConversation: props.onDeleteConversation,
    agentStatuses: props.agentStatuses,
    phases: props.phases,
    files: props.files,
    isRunning: props.isRunning,
    startedAt: props.startedAt,
  };

  return (
    <>
      <aside className="hidden w-[340px] flex-shrink-0 lg:block">
        <RailInner {...innerProps} />
      </aside>

      <AnimatePresence>
        {props.mobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={props.onCloseMobile}
              className="fixed inset-0 z-40 bg-black/45 lg:hidden"
            />
            <motion.div
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 30, stiffness: 300 }}
              className="fixed inset-y-0 right-0 z-50 w-[min(92vw,360px)] overflow-hidden lg:hidden"
            >
              <div className="flex h-full flex-col">
                <div className="flex items-center justify-end bg-transparent px-2 py-2">
                  <button
                    onClick={props.onCloseMobile}
                    className="rounded-2xl border border-white/10 bg-black/20 p-2 text-clai-text"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
                <div className="min-h-0 flex-1 overflow-hidden">
                  <RailInner {...innerProps} />
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
