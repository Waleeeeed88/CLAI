"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronRight, FileCode2, Check, X, Loader2 } from "lucide-react";
import { cn } from "../lib/cn";
import { ToolCallRecord } from "../lib/types";

const FILE_TOOLS = new Set(["write_file", "append_file", "delete_file", "read_file"]);

export function ToolCallBlock({ toolCall }: { toolCall: ToolCallRecord }) {
  const [open, setOpen] = useState(false);
  const isDone = toolCall.result !== undefined;
  const isFileTool = FILE_TOOLS.has(toolCall.tool);
  const filePath = toolCall.args?.file_path ?? toolCall.args?.path;

  return (
    <div className="my-1.5 rounded-lg border border-clai-border bg-clai-surface/40 text-[11px] font-mono overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2 px-3 py-2 hover:bg-clai-card/50 text-left transition-colors"
      >
        <ChevronRight
          className={cn(
            "w-3 h-3 text-clai-muted transition-transform",
            open && "rotate-90",
          )}
        />
        {isFileTool && <FileCode2 className="w-3.5 h-3.5 text-clai-muted" />}
        <span className="text-clai-text font-medium">{toolCall.tool}</span>
        {isFileTool && filePath && (
          <span className="text-clai-muted truncate max-w-[200px]">
            {filePath.split(/[\\/]/).pop()}
          </span>
        )}
        <span className="ml-auto flex-shrink-0">
          {!isDone && <Loader2 className="w-3 h-3 text-clai-text animate-spin" />}
          {isDone && toolCall.success && <Check className="w-3 h-3 text-clai-text" />}
          {isDone && !toolCall.success && <X className="w-3 h-3 text-clai-error" />}
        </span>
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="overflow-hidden"
          >
            <div className="px-3 pb-2.5 pt-1 border-t border-clai-border/60 space-y-1">
              {Object.entries(toolCall.args).map(([k, v]) => (
                <div key={k} className="flex gap-2">
                  <span className="text-clai-muted flex-shrink-0">{k}:</span>
                  <span className="text-clai-text break-all">{String(v)}</span>
                </div>
              ))}
              {toolCall.result && (
                <div className="mt-1.5 pt-1.5 border-t border-clai-border/40 text-clai-muted break-all max-h-32 overflow-y-auto">
                  {toolCall.result}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
