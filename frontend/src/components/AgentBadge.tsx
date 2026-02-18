export const AGENT_COLORS: Record<string, string> = {
  senior_dev: "#a78bfa",
  coder: "#60a5fa",
  coder_2: "#22d3ee",
  qa: "#34d399",
  ba: "#fbbf24",
  reviewer: "#fb7185",
};

export const AGENT_LABELS: Record<string, string> = {
  senior_dev: "Senior",
  coder: "Dev",
  coder_2: "Dev 2",
  qa: "QA",
  ba: "BA",
  reviewer: "Review",
};

export function AgentBadge({ agent }: { agent: string }) {
  const color = AGENT_COLORS[agent] ?? "#888";
  const label = AGENT_LABELS[agent] ?? agent;
  return (
    <span
      className="inline-flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider"
      style={{ color }}
    >
      <span
        className="w-1.5 h-1.5 rounded-full"
        style={{ backgroundColor: color }}
      />
      {label}
    </span>
  );
}
