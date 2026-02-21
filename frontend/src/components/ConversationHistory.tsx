"use client";

import { motion, AnimatePresence } from "framer-motion";
import { X, MessageSquare, Trash2 } from "lucide-react";
import { cn } from "../lib/cn";

export interface ConversationSummary {
  id: string;
  title: string;
  messageCount: number;
  createdAt: number;
}

interface Props {
  open: boolean;
  onClose: () => void;
  conversations: ConversationSummary[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
}

export function ConversationHistory({
  open,
  onClose,
  conversations,
  activeId,
  onSelect,
  onDelete,
}: Props) {
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
            initial={{ x: "-100%" }}
            animate={{ x: 0 }}
            exit={{ x: "-100%" }}
            transition={{ type: "spring", damping: 30, stiffness: 300 }}
            className="fixed left-0 top-0 bottom-0 z-50 w-72 border-r border-clai-border bg-clai-bg overflow-y-auto"
          >
            <div className="flex items-center justify-between px-4 py-3 border-b border-clai-border">
              <span className="text-xs font-semibold text-clai-text uppercase tracking-widest">
                History
              </span>
              <button onClick={onClose} className="p-1 rounded text-clai-muted hover:text-clai-text transition-colors">
                <X className="w-4 h-4" />
              </button>
            </div>

            {conversations.length === 0 ? (
              <div className="px-4 py-8 text-center text-xs text-clai-muted">
                No conversations yet. Start a new chat to see history here.
              </div>
            ) : (
              <div className="p-2 space-y-1">
                {conversations.map((conv) => (
                  <div
                    key={conv.id}
                    className={cn(
                      "group flex items-start gap-2 rounded-lg px-3 py-2.5 cursor-pointer transition-colors",
                      conv.id === activeId
                        ? "bg-clai-accent/10 border border-clai-accent/20"
                        : "hover:bg-clai-surface border border-transparent",
                    )}
                    onClick={() => {
                      onSelect(conv.id);
                      onClose();
                    }}
                  >
                    <MessageSquare className="w-3.5 h-3.5 text-clai-muted mt-0.5 flex-shrink-0" />
                    <div className="min-w-0 flex-1">
                      <div className="text-xs text-clai-text truncate font-medium">
                        {conv.title}
                      </div>
                      <div className="text-[10px] text-clai-muted mt-0.5">
                        {conv.messageCount} messages &middot;{" "}
                        {new Date(conv.createdAt).toLocaleDateString()}
                      </div>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDelete(conv.id);
                      }}
                      className="opacity-0 group-hover:opacity-100 p-1 rounded text-clai-muted hover:text-clai-error transition-all"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
