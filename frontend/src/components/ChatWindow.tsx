"use client";

import { useEffect, useRef, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, XCircle } from "lucide-react";
import { ChatMessage, PhaseEvent, FileEntry } from "../lib/types";
import { MessageBubble } from "./MessageBubble";
import { AgentActivityCard } from "./AgentActivityCard";
import { PhaseTimeline } from "./PhaseTimeline";
import { WelcomeScreen } from "./WelcomeScreen";
import { type PhaseId } from "../lib/constants";
import type { ConversationSummary } from "../lib/storage";

interface Props {
  messages: ChatMessage[];
  phases: PhaseEvent[];
  files: FileEntry[];
  isRunning: boolean;
  error: string | null;
  startedAt: number | null;
  onSuggestionSelect: (prompt: string, phases: PhaseId[]) => void;
  recentConversations?: ConversationSummary[];
  onSelectConversation?: (id: string) => void;
}

export function ChatWindow({
  messages,
  phases,
  files,
  isRunning,
  error,
  startedAt,
  onSuggestionSelect,
  recentConversations,
  onSelectConversation,
}: Props) {
  const endRef = useRef<HTMLDivElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const pinned = useRef(true);

  useEffect(() => {
    if (pinned.current) endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, phases.length]);

  const onScroll = () => {
    const el = scrollRef.current;
    if (el) pinned.current = el.scrollHeight - el.scrollTop - el.clientHeight < 96;
  };

  const empty = messages.length === 0 && phases.length === 0 && !isRunning;

  return (
    <div
      ref={scrollRef}
      onScroll={onScroll}
      className="flex-1 overflow-y-auto px-3 py-3 lg:px-5 lg:py-5"
    >
      {empty ? (
        <WelcomeScreen
          onSelect={onSuggestionSelect}
          recentConversations={recentConversations}
          onSelectConversation={onSelectConversation}
        />
      ) : (
        <div className="mx-auto flex max-w-5xl flex-col gap-4">
          {phases.length > 0 && (
            <div className="panel-shell glass-line rounded-[28px] border border-white/8 bg-white/[0.04] px-4 py-3">
              <PhaseTimeline phases={phases} />
            </div>
          )}

          <div className="rounded-[32px] border border-white/8 bg-white/[0.025] p-3 sm:p-4 lg:p-5">
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

            {error && (
              <div className="mt-4 rounded-[22px] border border-clai-error/20 bg-clai-error/10 px-4 py-3 text-sm text-clai-error">
                {error}
              </div>
            )}

            {!isRunning && messages.length > 0 && !messages.some((m) => m.isStreaming) && (
              <CompletionSummary
                messages={messages}
                phases={phases}
                files={files}
                error={error}
                startedAt={startedAt}
              />
            )}

            <div ref={endRef} className="h-4" />
          </div>
        </div>
      )}
    </div>
  );
}

function CompletionSummary({
  messages,
  phases,
  files,
  error,
  startedAt,
}: {
  messages: ChatMessage[];
  phases: PhaseEvent[];
  files: FileEntry[];
  error: string | null;
  startedAt: number | null;
}) {
  const totalTokens = useMemo(
    () => messages.reduce((sum, message) => sum + (message.tokens ?? 0), 0),
    [messages],
  );
  const totalDuration = useMemo(
    () => phases.reduce((sum, phase) => sum + (phase.duration ?? 0), 0),
    [phases],
  );
  const doneFiles = files.filter((file) => file.status === "done").length;
  const hasError = Boolean(error);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={hasError
        ? "mt-5 rounded-[24px] border border-clai-error/20 bg-clai-error/10 p-4"
        : "mt-5 rounded-[24px] border border-white/8 bg-white/[0.04] p-4"}
    >
      <div className="flex items-center gap-2">
        {hasError ? (
          <XCircle className="h-4 w-4 text-clai-error" />
        ) : (
          <CheckCircle2 className="h-4 w-4 text-clai-text" />
        )}
        <span className={hasError ? "text-sm font-medium text-clai-error" : "text-sm font-medium text-clai-text"}>
          {hasError ? "Pipeline completed with issues" : "Pipeline completed"}
        </span>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-4">
        <SummaryMetric label="Responses" value={`${messages.length}`} />
        <SummaryMetric label="Files" value={`${doneFiles}`} />
        <SummaryMetric
          label={totalTokens > 0 ? "Tokens" : "Duration"}
          value={totalTokens > 0 ? totalTokens.toLocaleString() : totalDuration > 0 ? `${totalDuration.toFixed(0)}s` : "--"}
        />
        <SummaryMetric
          label="Started"
          value={startedAt ? new Date(startedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "--"}
        />
      </div>
    </motion.div>
  );
}

function SummaryMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[18px] border border-white/8 bg-black/10 px-3 py-3 text-center">
      <p className="text-[10px] uppercase tracking-[0.18em] text-clai-muted">{label}</p>
      <p className="mt-1 text-lg font-semibold text-clai-text">{value}</p>
    </div>
  );
}
