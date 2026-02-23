"use client";

import { useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Crown, Code2, Braces, TestTube2, FileSearch, Eye,
  FileCode2, Clock, Zap, CheckCircle2,
} from "lucide-react";
import { cn } from "../lib/cn";
import { AGENTS, type AgentRole } from "../lib/constants";
import { FileEntry, PhaseEvent } from "../lib/types";

type AgentStatus = "idle" | "thinking" | "using_tool";

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  Crown, Code2, Braces, TestTube2, FileSearch, Eye,
};

const STATUS_STYLES = {
  idle: "text-slate-500",
  thinking: "text-cyan-400",
  using_tool: "text-emerald-400",
} as const;

const STATUS_DOT = {
  idle: "bg-slate-600",
  thinking: "bg-cyan-400 animate-pulse",
  using_tool: "bg-emerald-400 animate-pulse",
} as const;

interface Props {
  agentStatuses: Record<AgentRole, AgentStatus>;
  phases: PhaseEvent[];
  files: FileEntry[];
  isRunning: boolean;
  startedAt: number | null;
}

function useElapsed(startedAt: number | null, isRunning: boolean) {
  // Re-render every second while running
  const [, setTick] = useMemo(() => {
    if (!startedAt || !isRunning) return [0, () => {}];
    // This is a hack to force re-render — we use the parent's render cycle
    return [0, () => {}];
  }, [startedAt, isRunning]);

  if (!startedAt) return null;
  const elapsed = Math.floor((Date.now() - startedAt) / 1000);
  const mins = Math.floor(elapsed / 60);
  const secs = elapsed % 60;
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

function formatPhase(phase: string) {
  return phase.split("_").map((p) => p.charAt(0).toUpperCase() + p.slice(1)).join(" ");
}

const PHASE_STATUS_STYLE: Record<string, string> = {
  running: "border-cyan-400/30 bg-cyan-400/10 text-cyan-300",
  done: "border-emerald-400/30 bg-emerald-400/10 text-emerald-300",
  completed: "border-emerald-400/30 bg-emerald-400/10 text-emerald-300",
  success: "border-emerald-400/30 bg-emerald-400/10 text-emerald-300",
  failed: "border-red-400/30 bg-red-400/10 text-red-300",
};

export function ExecutionPanel({ agentStatuses, phases, files, isRunning, startedAt }: Props) {
  const elapsed = useElapsed(startedAt, isRunning);
  const agentEntries = Object.entries(AGENTS) as [AgentRole, (typeof AGENTS)[AgentRole]][];
  const activeCount = Object.values(agentStatuses).filter((s) => s !== "idle").length;
  const doneFiles = files.filter((f) => f.status === "done").length;
  const totalTokens = 0; // TODO: aggregate from messages if needed
  const recentFiles = [...files].sort((a, b) => b.timestamp - a.timestamp).slice(0, 8);

  return (
    <motion.aside
      initial={{ width: 0, opacity: 0 }}
      animate={{ width: 280, opacity: 1 }}
      exit={{ width: 0, opacity: 0 }}
      transition={{ type: "spring", damping: 30, stiffness: 300 }}
      className="hidden lg:flex flex-col border-l border-clai-border bg-clai-surface/50 backdrop-blur-sm overflow-hidden flex-shrink-0"
    >
      <div className="flex-1 overflow-y-auto p-3 space-y-4">
        {/* Status header */}
        <div className="rounded-xl border border-clai-border bg-clai-card/60 p-3">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              {isRunning ? (
                <span className="flex items-center gap-1.5 text-[11px] text-cyan-300 font-mono">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
                  Running
                </span>
              ) : (
                <span className="flex items-center gap-1.5 text-[11px] text-emerald-300 font-mono">
                  <CheckCircle2 className="w-3 h-3" />
                  Complete
                </span>
              )}
            </div>
            {elapsed && (
              <span className="flex items-center gap-1 text-[11px] text-clai-muted font-mono">
                <Clock className="w-3 h-3" />
                {elapsed}
              </span>
            )}
          </div>
          <div className="grid grid-cols-2 gap-2 text-[11px]">
            <div className="rounded-lg bg-clai-surface/60 px-2 py-1.5 text-center">
              <p className="text-clai-muted">Agents</p>
              <p className="text-sm font-semibold text-clai-text">{activeCount}/{agentEntries.length}</p>
            </div>
            <div className="rounded-lg bg-clai-surface/60 px-2 py-1.5 text-center">
              <p className="text-clai-muted">Files</p>
              <p className="text-sm font-semibold text-clai-text">{doneFiles}/{files.length}</p>
            </div>
          </div>
        </div>

        {/* Agent statuses */}
        <div>
          <h3 className="text-[10px] uppercase tracking-widest text-clai-muted mb-2 px-1">
            Team
          </h3>
          <div className="space-y-1">
            {agentEntries.map(([role, meta]) => {
              const Icon = ICON_MAP[meta.icon] ?? Code2;
              const status = agentStatuses[role];
              return (
                <div
                  key={role}
                  className={cn(
                    "flex items-center gap-2.5 rounded-lg px-2.5 py-2 transition-colors",
                    status !== "idle" ? "bg-clai-card/60 border border-clai-border/60" : "",
                  )}
                >
                  <span
                    className="flex h-6 w-6 items-center justify-center rounded-md"
                    style={{ backgroundColor: `${meta.color}18`, color: meta.color }}
                  >
                    <Icon className="h-3.5 w-3.5" />
                  </span>
                  <span className={cn("text-xs flex-1", STATUS_STYLES[status])}>
                    {meta.label}
                  </span>
                  <span className={cn("w-1.5 h-1.5 rounded-full", STATUS_DOT[status])} />
                </div>
              );
            })}
          </div>
        </div>

        {/* Phase progress */}
        {phases.length > 0 && (
          <div>
            <h3 className="text-[10px] uppercase tracking-widest text-clai-muted mb-2 px-1">
              Phases
            </h3>
            <div className="space-y-1.5">
              {phases.map((p, i) => {
                const statusKey = (p.status ?? "running").toLowerCase();
                const style = PHASE_STATUS_STYLE[statusKey] ?? PHASE_STATUS_STYLE.running;
                return (
                  <div
                    key={`${p.phase}-${i}`}
                    className={cn("rounded-lg border px-2.5 py-2 text-[11px]", style)}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{formatPhase(p.phase)}</span>
                      {p.duration != null && (
                        <span className="text-[10px] font-mono opacity-70">
                          {p.duration.toFixed(1)}s
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* File activity */}
        {files.length > 0 && (
          <div>
            <h3 className="text-[10px] uppercase tracking-widest text-clai-muted mb-2 px-1">
              Files ({doneFiles}/{files.length})
            </h3>
            <div className="space-y-1">
              {recentFiles.map((f) => {
                const name = f.path.split(/[\\/]/).pop() ?? f.path;
                const agentMeta = AGENTS[f.agent as AgentRole];
                return (
                  <div
                    key={f.id}
                    className="flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-[11px]"
                  >
                    <FileCode2 className="w-3 h-3 text-clai-muted flex-shrink-0" />
                    <span className="text-clai-text truncate flex-1 font-mono" title={f.path}>
                      {name}
                    </span>
                    <span
                      className={cn(
                        "w-1.5 h-1.5 rounded-full flex-shrink-0",
                        f.status === "done" && "bg-emerald-400",
                        f.status === "writing" && "bg-cyan-400 animate-pulse",
                        f.status === "error" && "bg-red-400",
                      )}
                    />
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </motion.aside>
  );
}
