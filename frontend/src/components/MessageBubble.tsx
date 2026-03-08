"use client";

import { motion } from "framer-motion";
import { ChatMessage } from "../lib/types";
import { AgentBadge } from "./AgentBadge";
import { ToolCallBlock } from "./ToolCallBlock";
import { MarkdownRenderer } from "./MarkdownRenderer";

export function MessageBubble({ message }: { message: ChatMessage }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="mb-3 rounded-[24px] border border-white/6 bg-white/[0.025] px-4 py-4 last:mb-0"
    >
      {/* Header */}
      <div className="mb-3 flex items-center gap-2">
        <AgentBadge agent={message.agent} />
        {message.model && (
          <span className="text-[10px] text-clai-muted font-mono">
            {message.model.split("-").slice(-2).join("-")}
          </span>
        )}
        {message.tokens != null && (
          <span className="text-[10px] text-clai-muted ml-auto font-mono tabular-nums">
            {message.tokens.toLocaleString()} tok
          </span>
        )}
      </div>

      {/* Tool calls */}
      {message.toolCalls.length > 0 && (
        <div className="mb-2">
          {message.toolCalls.map((tc, i) => (
            <ToolCallBlock key={i} toolCall={tc} />
          ))}
        </div>
      )}

      {/* Content */}
      {message.content && (
        <div>
          <MarkdownRenderer content={message.content} />
        </div>
      )}
    </motion.div>
  );
}
