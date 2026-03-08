"use client";

import { motion } from "framer-motion";
import {
  Rocket, Search, Cpu, TestTube2, GitBranch,
  MessageSquare, Clock,
} from "lucide-react";
import { cn } from "../lib/cn";
import { SUGGESTION_CARDS, type PhaseId } from "../lib/constants";
import type { ConversationSummary } from "../lib/storage";

const ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  "new-project": Rocket,
  "code-review": Search,
  "architecture": Cpu,
  "testing": TestTube2,
  "github-sync": GitBranch,
};

interface Props {
  onSelect: (prompt: string, phases: PhaseId[]) => void;
  recentConversations?: ConversationSummary[];
  onSelectConversation?: (id: string) => void;
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

export function WelcomeScreen({ onSelect, recentConversations, onSelectConversation }: Props) {
  const hasRecent = recentConversations && recentConversations.length > 0;

  return (
    <div className="mx-auto flex min-h-full w-full max-w-5xl flex-col justify-center px-4 py-10">
      <motion.section
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        className="rounded-[32px] border border-white/8 bg-white/[0.03] p-6 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] sm:p-8"
      >
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-2xl">
            <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.04]">
              <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-white text-clai-bg">
                <span className="text-sm font-bold text-clai-bg">C</span>
              </div>
            </div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-clai-muted">
              Start A New Run
            </p>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight text-clai-text sm:text-4xl">
              What should CLAI do next?
            </h1>
            <p className="mt-3 max-w-xl text-sm leading-7 text-clai-muted sm:text-[15px]">
              CLAI can plan a project, implement code, review an existing codebase,
              generate QA coverage, and prepare GitHub-ready output. Pick a starting
              point below or type your own request in the composer.
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 lg:w-[320px] lg:grid-cols-1">
            <CapabilityChip label="Plan and architect" />
            <CapabilityChip label="Build and refactor code" />
            <CapabilityChip label="Review and test" />
            <CapabilityChip label="Prepare GitHub output" />
          </div>
        </div>

        <div className="mt-8">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-[11px] font-semibold uppercase tracking-[0.24em] text-clai-muted">
              What CLAI Can Do
            </h2>
          </div>
          <div className="grid w-full grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {SUGGESTION_CARDS.map((card, i) => {
              const Icon = ICONS[card.id] ?? Rocket;
              return (
                <motion.button
                  key={card.id}
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.35, delay: 0.06 * i, ease: "easeOut" }}
                  onClick={() => onSelect(card.prompt, [...card.phases])}
                  className={cn(
                    "group rounded-[24px] border border-clai-border bg-clai-surface/70 p-5 text-left",
                    "hover:border-white/14 hover:bg-white/[0.045] transition-all duration-200",
                  )}
                >
                  <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-2xl border border-white/8 bg-white/[0.04]">
                    <Icon className="h-4 w-4 text-clai-text" />
                  </div>
                  <div className="text-base font-semibold text-clai-text">{card.title}</div>
                  <p className="mt-2 text-sm leading-6 text-clai-muted">{card.description}</p>
                </motion.button>
              );
            })}
          </div>
        </div>
      </motion.section>

      {hasRecent && (
        <motion.section
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, delay: 0.4, ease: "easeOut" }}
          className="mt-6 rounded-[28px] border border-white/8 bg-white/[0.025] p-5"
        >
          <h3 className="mb-4 text-[11px] font-semibold uppercase tracking-[0.24em] text-clai-muted">
            Recent Sessions
          </h3>
          <div className="space-y-2">
            {recentConversations!.map((conv) => (
              <button
                key={conv.id}
                onClick={() => onSelectConversation?.(conv.id)}
                className="group flex w-full items-center gap-3 rounded-2xl border border-clai-border/60 bg-clai-surface/40 px-4 py-3 text-left transition-all hover:border-white/14 hover:bg-white/[0.04]"
              >
                <span className="flex h-9 w-9 items-center justify-center rounded-2xl border border-white/8 bg-white/[0.04]">
                  <MessageSquare className="h-4 w-4 text-clai-text" />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-clai-text">{conv.title}</p>
                  <p className="text-[11px] text-clai-muted">{conv.messageCount} messages</p>
                </div>
                <span className="flex flex-shrink-0 items-center gap-1 text-[10px] text-clai-muted">
                  <Clock className="h-3 w-3" />
                  {timeAgo(conv.updatedAt)}
                </span>
              </button>
            ))}
          </div>
        </motion.section>
      )}
    </div>
  );
}

function CapabilityChip({ label }: { label: string }) {
  return (
    <div className="rounded-2xl border border-white/8 bg-black/15 px-4 py-3 text-sm text-clai-text">
      {label}
    </div>
  );
}
