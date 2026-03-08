"use client";

import {
  Crown, Code2, Braces, Sparkles, TestTube2, FileSearch, Eye,
} from "lucide-react";
import { AGENTS, type AgentRole } from "../lib/constants";

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
  agent: string;
  showLabel?: boolean;
}

export function AgentBadge({ agent, showLabel = true }: Props) {
  const meta = AGENTS[agent as AgentRole];
  const color = meta?.color ?? "#888";
  const label = meta?.label ?? agent;
  const Icon = meta ? ICON_MAP[meta.icon] ?? Code2 : Code2;

  return (
    <span className="inline-flex items-center gap-2 text-[11px] font-semibold">
      <span
        className="flex h-8 w-8 items-center justify-center rounded-2xl border border-white/6"
        style={{ backgroundColor: `${color}14`, color }}
      >
        <Icon className="h-4 w-4" />
      </span>
      {showLabel && (
        <span className="rounded-full border border-white/6 bg-white/[0.04] px-2.5 py-1 uppercase tracking-[0.18em] text-clai-text">
          {label}
        </span>
      )}
    </span>
  );
}
