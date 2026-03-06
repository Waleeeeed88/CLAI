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
    <div className="flex flex-1 flex-col items-center justify-center px-4 py-8 select-none">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        className="text-center mb-8"
      >
        <div className="w-14 h-14 mx-auto mb-5 rounded-2xl bg-gradient-to-br from-cyan-500/20 to-blue-600/20 border border-cyan-500/20 flex items-center justify-center">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
            <span className="text-white font-bold text-sm">C</span>
          </div>
        </div>
        <h1 className="text-xl font-semibold text-clai-text mb-1.5">
          What should we build?
        </h1>
        <p className="text-sm text-clai-muted max-w-md">
          Pick a workflow or describe your project below.
        </p>
      </motion.div>

      {/* Suggestion cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 max-w-2xl w-full">
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
                "group text-left rounded-xl border border-clai-border bg-clai-surface/60 p-4",
                "hover:border-clai-accent/30 hover:bg-clai-surface transition-all duration-200",
              )}
            >
              <div className="flex items-center gap-2.5 mb-2">
                <div className="w-8 h-8 rounded-lg bg-clai-card border border-clai-border flex items-center justify-center group-hover:border-clai-accent/30 transition-colors">
                  <Icon className="w-4 h-4 text-clai-muted group-hover:text-clai-accent transition-colors" />
                </div>
                <span className="text-sm font-medium text-clai-text">{card.title}</span>
              </div>
              <p className="text-xs text-clai-muted leading-relaxed">{card.description}</p>
            </motion.button>
          );
        })}
      </div>

      {/* Recent sessions */}
      {hasRecent && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, delay: 0.4, ease: "easeOut" }}
          className="mt-8 w-full max-w-2xl"
        >
          <h3 className="text-[10px] uppercase tracking-widest text-clai-muted mb-3 px-1">
            Recent Sessions
          </h3>
          <div className="space-y-1.5">
            {recentConversations!.map((conv) => (
              <button
                key={conv.id}
                onClick={() => onSelectConversation?.(conv.id)}
                className="w-full text-left flex items-center gap-3 rounded-xl border border-clai-border/60 bg-clai-surface/40 px-4 py-3 hover:border-clai-accent/20 hover:bg-clai-surface/60 transition-all group"
              >
                <MessageSquare className="w-4 h-4 text-clai-muted group-hover:text-clai-accent flex-shrink-0 transition-colors" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-clai-text truncate">{conv.title}</p>
                  <p className="text-[11px] text-clai-muted">
                    {conv.messageCount} messages
                  </p>
                </div>
                <span className="flex items-center gap-1 text-[10px] text-clai-muted flex-shrink-0">
                  <Clock className="w-3 h-3" />
                  {timeAgo(conv.updatedAt)}
                </span>
              </button>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}
