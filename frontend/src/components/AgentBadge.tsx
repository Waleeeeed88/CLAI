"use client";

import {
  Crown, Code2, Braces, TestTube2, FileSearch, Eye,
} from "lucide-react";
import { AGENTS, type AgentRole } from "../lib/constants";

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
  showLabel?: boolean;
}

export function AgentBadge({ agent, showLabel = true }: Props) {
  const meta = AGENTS[agent as AgentRole];
  const color = meta?.color ?? "#888";
  const label = meta?.label ?? agent;
  const Icon = meta ? ICON_MAP[meta.icon] ?? Code2 : Code2;

  return (
    <span
      className="inline-flex items-center gap-1.5 text-[11px] font-semibold"
      style={{ color }}
    >
      <span
        className="w-5 h-5 rounded-md flex items-center justify-center"
        style={{ backgroundColor: color + "18" }}
      >
        <Icon className="w-3 h-3" />
      </span>
      {showLabel && <span className="uppercase tracking-wider text-[10px]">{label}</span>}
    </span>
  );
}
