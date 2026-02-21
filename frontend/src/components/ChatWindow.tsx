"use client";

import { useEffect, useRef } from "react";
import { AnimatePresence } from "framer-motion";
import { ChatMessage, PhaseEvent } from "../lib/types";
import { MessageBubble } from "./MessageBubble";
import { AgentActivityCard } from "./AgentActivityCard";
import { PhaseTimeline } from "./PhaseTimeline";
import { WelcomeScreen } from "./WelcomeScreen";
import { type PhaseId } from "../lib/constants";

interface Props {
  messages: ChatMessage[];
  phases: PhaseEvent[];
  isRunning: boolean;
  error: string | null;
  onSuggestionSelect: (prompt: string, phases: PhaseId[]) => void;
}

export function ChatWindow({
  messages,
  phases,
  isRunning,
  error,
  onSuggestionSelect,
}: Props) {
  const endRef = useRef<HTMLDivElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const pinned = useRef(true);

  useEffect(() => {
    if (pinned.current) endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, phases.length]);

  const onScroll = () => {
    const el = scrollRef.current;
    if (el) pinned.current = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
  };

  const empty = messages.length === 0 && phases.length === 0 && !isRunning;

  return (
    <div
      ref={scrollRef}
      onScroll={onScroll}
      className="flex-1 overflow-y-auto bg-clai-bg"
    >
      {empty ? (
        <WelcomeScreen onSelect={onSuggestionSelect} />
      ) : (
        <div className="max-w-3xl mx-auto px-4 py-4">
          {/* Phase timeline */}
          {phases.length > 0 && (
            <div className="mb-4 rounded-xl border border-clai-border bg-clai-surface/40 py-2">
              <PhaseTimeline phases={phases} />
            </div>
          )}

          {/* Messages — streaming ones show as activity cards */}
          <AnimatePresence mode="popLayout">
            {messages.map((msg) =>
              msg.isStreaming ? (
                <AgentActivityCard
                  key={msg.id}
                  agent={msg.agent}
                  toolCalls={msg.toolCalls}
                />
              ) : (
                <MessageBubble key={msg.id} message={msg} />
              ),
            )}
          </AnimatePresence>

          {/* Error display */}
          {error && (
            <div className="mt-3 rounded-lg border border-clai-error/20 bg-clai-error/5 px-4 py-3 text-sm text-clai-error">
              {error}
            </div>
          )}

          <div ref={endRef} className="h-4" />
        </div>
      )}
    </div>
  );
}
