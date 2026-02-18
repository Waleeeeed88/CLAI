"use client";
import { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import { ChatMessage } from "../lib/types";
import { AgentBadge } from "./AgentBadge";
import { ToolCallBlock } from "./ToolCallBlock";

function StreamedContent({ content }: { content: string }) {
  const [pos, setPos] = useState(0);
  const ref = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    setPos(0);
    ref.current = setInterval(() => {
      setPos((p) => {
        if (p >= content.length) {
          if (ref.current) clearInterval(ref.current);
          return content.length;
        }
        return p + 50;
      });
    }, 16);
    return () => {
      if (ref.current) clearInterval(ref.current);
    };
  }, [content]);

  return (
    <div className="prose prose-sm max-w-none mt-1.5">
      <ReactMarkdown>{content.slice(0, pos)}</ReactMarkdown>
    </div>
  );
}

export function MessageBubble({ message }: { message: ChatMessage }) {
  return (
    <div className="py-3 border-b border-[#12121e] last:border-0 animate-in fade-in">
      <div className="flex items-center gap-2 mb-1.5">
        <AgentBadge agent={message.agent} />
        {message.model && (
          <span className="text-[10px] text-[#303048] font-mono">
            {message.model.split("-").slice(-2).join("-")}
          </span>
        )}
        {message.tokens != null && (
          <span className="text-[10px] text-[#303048] ml-auto font-mono tabular-nums">
            {message.tokens.toLocaleString()} tok
          </span>
        )}
      </div>

      {message.toolCalls.map((tc, i) => (
        <ToolCallBlock key={i} toolCall={tc} />
      ))}

      {message.isStreaming && !message.content ? (
        <span className="text-[#303048] text-sm animate-pulse">thinking...</span>
      ) : message.content ? (
        <StreamedContent content={message.content} />
      ) : null}
    </div>
  );
}
