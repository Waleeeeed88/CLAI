"use client";

import { motion } from "framer-motion";
import {
  Rocket, Search, Cpu, TestTube2, GitBranch,
} from "lucide-react";
import { cn } from "../lib/cn";
import { SUGGESTION_CARDS, type PhaseId } from "../lib/constants";

const ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  "new-project": Rocket,
  "code-review": Search,
  "architecture": Cpu,
  "testing": TestTube2,
  "github-sync": GitBranch,
};

interface Props {
  onSelect: (prompt: string, phases: PhaseId[]) => void;
}

export function WelcomeScreen({ onSelect }: Props) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center px-4 py-12 select-none">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        className="text-center mb-10"
      >
        <div className="w-14 h-14 mx-auto mb-5 rounded-2xl bg-gradient-to-br from-cyan-500/20 to-blue-600/20 border border-cyan-500/20 flex items-center justify-center">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
            <span className="text-white font-bold text-sm">C</span>
          </div>
        </div>
        <h1 className="text-xl font-semibold text-clai-text mb-1.5">
          Welcome back. How can I help?
        </h1>
        <p className="text-sm text-clai-muted max-w-md">
          Select a workflow below, or describe what you need in the input.
        </p>
      </motion.div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 max-w-2xl w-full">
        {SUGGESTION_CARDS.map((card, i) => {
          const Icon = ICONS[card.id] ?? Rocket;
          return (
            <motion.button
              key={card.id}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.35, delay: 0.08 * i, ease: "easeOut" }}
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
    </div>
  );
}
