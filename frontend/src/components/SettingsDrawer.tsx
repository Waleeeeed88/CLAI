"use client";

import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";

interface Props {
  open: boolean;
  onClose: () => void;
}

export function SettingsDrawer({ open, onClose }: Props) {
  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-40 bg-black/30"
          />
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 30, stiffness: 300 }}
            className="fixed right-0 top-0 bottom-0 z-50 w-80 border-l border-clai-border bg-clai-bg overflow-y-auto"
          >
            <div className="flex items-center justify-between px-4 py-3 border-b border-clai-border">
              <span className="text-xs font-semibold text-clai-text uppercase tracking-widest">
                Settings
              </span>
              <button onClick={onClose} className="p-1 rounded text-clai-muted hover:text-clai-text transition-colors">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-4 space-y-6">
              <div>
                <h4 className="text-[10px] uppercase tracking-widest text-clai-muted mb-3">
                  About
                </h4>
                <p className="text-xs text-clai-text leading-relaxed">
                  CLAI is a multi-agent AI orchestration system. Configure your
                  project settings using the input bar below. Use the gear icon
                  next to the input to set project name, workspace, and GitHub
                  integration.
                </p>
              </div>

              <div>
                <h4 className="text-[10px] uppercase tracking-widest text-clai-muted mb-3">
                  Agents
                </h4>
                <div className="space-y-2 text-xs text-clai-text">
                  <AgentInfo name="Senior Dev" model="Claude Opus" color="#a78bfa" />
                  <AgentInfo name="Coder" model="Claude Sonnet" color="#60a5fa" />
                  <AgentInfo name="Coder 2" model="Gemini Pro" color="#22d3ee" />
                  <AgentInfo name="QA" model="Gemini Flash" color="#34d399" />
                  <AgentInfo name="Analyst" model="GPT 5.2" color="#fbbf24" />
                  <AgentInfo name="Reviewer" model="Claude Sonnet" color="#fb7185" />
                </div>
              </div>

              <div>
                <h4 className="text-[10px] uppercase tracking-widest text-clai-muted mb-3">
                  Keyboard Shortcuts
                </h4>
                <div className="space-y-1.5 text-xs">
                  <Shortcut keys="Enter" action="Send message" />
                  <Shortcut keys="Shift + Enter" action="New line" />
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

function AgentInfo({ name, model, color }: { name: string; model: string; color: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
      <span className="font-medium">{name}</span>
      <span className="text-clai-muted ml-auto">{model}</span>
    </div>
  );
}

function Shortcut({ keys, action }: { keys: string; action: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-clai-muted">{action}</span>
      <kbd className="rounded border border-clai-border bg-clai-surface px-1.5 py-0.5 text-[10px] font-mono text-clai-text">
        {keys}
      </kbd>
    </div>
  );
}
