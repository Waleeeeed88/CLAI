"use client";

import { motion } from "framer-motion";
import {
  Crown, Code2, Braces, TestTube2, FileSearch, Eye,
} from "lucide-react";
import { AGENTS, type AgentRole } from "../lib/constants";
import { cn } from "../lib/cn";
import { ToolCallRecord } from "../lib/types";

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  Crown,
  Code2,
  Braces,
  TestTube2,
  FileSearch,
  Eye,
};

interface Props {
  agent: string;
  toolCalls: ToolCallRecord[];
}

export function AgentActivityCard({ agent, toolCalls }: Props) {
  const meta = AGENTS[agent as AgentRole];
  const color = meta?.color ?? "#888";
  const label = meta?.label ?? agent;
  const Icon = meta ? ICON_MAP[meta.icon] ?? Code2 : Code2;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="py-3 border-b border-clai-border/50 last:border-0"
    >
      <div className="flex items-center gap-3 mb-2">
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center agent-pulse"
          style={{
            backgroundColor: color + "15",
            borderColor: color + "30",
            borderWidth: 1,
            ["--agent-color" as string]: color,
          }}
        >
          <Icon className="w-4 h-4" style={{ color }} />
        </div>
        <div>
          <span className="text-sm font-medium" style={{ color }}>
            {label}
          </span>
          <div className="flex items-center gap-1.5 mt-0.5">
            <div className="flex gap-0.5">
              <span className="typing-dot w-1 h-1 rounded-full bg-clai-muted" />
              <span className="typing-dot w-1 h-1 rounded-full bg-clai-muted" />
              <span className="typing-dot w-1 h-1 rounded-full bg-clai-muted" />
            </div>
            <span className="text-[11px] text-clai-muted">thinking</span>
          </div>
        </div>
      </div>

      {/* Live tool pills */}
      {toolCalls.length > 0 && (
        <div className="flex flex-wrap gap-1.5 ml-11">
          {toolCalls.map((tc, i) => {
            const isDone = tc.result !== undefined;
            return (
              <motion.span
                key={i}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.15 }}
                className={cn(
                  "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-mono border",
                  isDone && tc.success
                    ? "border-clai-success/30 bg-clai-success/5 text-clai-success"
                    : isDone && !tc.success
                    ? "border-clai-error/30 bg-clai-error/5 text-clai-error"
                    : "border-clai-accent/30 bg-clai-accent/5 text-clai-accent",
                )}
              >
                {!isDone && (
                  <span className="w-1 h-1 rounded-full bg-current animate-pulse" />
                )}
                {tc.tool}
              </motion.span>
            );
          })}
        </div>
      )}
    </motion.div>
  );
}
