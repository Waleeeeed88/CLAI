"use client";

import { motion, AnimatePresence } from "framer-motion";
import { X, FileCode2 } from "lucide-react";
import { FileEntry } from "../lib/types";
import { AGENTS, type AgentRole } from "../lib/constants";
import { cn } from "../lib/cn";

interface Props {
  files: FileEntry[];
  open: boolean;
  onClose: () => void;
}

export function FilesPanel({ files, open, onClose }: Props) {
  const sorted = [...files].sort((a, b) => b.timestamp - a.timestamp);

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
                File Activity ({files.length})
              </span>
              <button onClick={onClose} className="p-1 rounded text-clai-muted hover:text-clai-text transition-colors">
                <X className="w-4 h-4" />
              </button>
            </div>

            {files.length === 0 ? (
              <div className="px-4 py-8 text-center text-xs text-clai-muted">
                File operations will appear here once tools start writing.
              </div>
            ) : (
              <div className="p-3 space-y-1.5">
                {sorted.map((f) => {
                  const nameParts = f.path.split(/[\\/]/g);
                  const name = nameParts[nameParts.length - 1] ?? f.path;
                  const parent = nameParts.length > 1 ? nameParts.slice(0, -1).join("/") : "";
                  const agentMeta = AGENTS[f.agent as AgentRole];
                  const color = agentMeta?.color ?? "#666";
                  const agentLabel = agentMeta?.label ?? f.agent;

                  return (
                    <motion.div
                      key={f.id}
                      initial={{ opacity: 0, x: 12 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="rounded-lg border border-clai-border bg-clai-surface p-2.5 text-[11px]"
                    >
                      <div className="flex items-center gap-2">
                        <FileCode2 className="w-3.5 h-3.5 text-clai-muted flex-shrink-0" />
                        <span className="text-clai-text font-medium truncate" title={f.path}>
                          {name}
                        </span>
                        <span
                          className={cn(
                            "ml-auto rounded-full px-2 py-0.5 text-[9px] font-semibold border flex-shrink-0",
                            f.status === "done" && "border-clai-success/30 bg-clai-success/10 text-clai-success",
                            f.status === "writing" && "border-clai-accent/30 bg-clai-accent/10 text-clai-accent",
                            f.status === "error" && "border-clai-error/30 bg-clai-error/10 text-clai-error",
                          )}
                        >
                          {f.status}
                        </span>
                      </div>
                      <div className="mt-1 flex items-center gap-2 text-[10px]">
                        <span className="text-clai-muted truncate" title={parent}>
                          {parent || "root"}
                        </span>
                        <span className="ml-auto font-semibold" style={{ color }}>
                          {agentLabel}
                        </span>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            )}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
