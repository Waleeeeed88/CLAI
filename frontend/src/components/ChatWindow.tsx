"use client";

import { useEffect, useRef, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, XCircle, FileCode2, Clock } from "lucide-react";
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
        <WelcomeScreen
          onSelect={onSuggestionSelect}
          recentConversations={recentConversations}
          onSelectConversation={onSelectConversation}
        />
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

          {/* Completion summary */}
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
    () => messages.reduce((sum, m) => sum + (m.tokens ?? 0), 0),
    [messages],
  );
  const totalDuration = useMemo(
    () => phases.reduce((sum, p) => sum + (p.duration ?? 0), 0),
    [phases],
  );
  const doneFiles = files.filter((f) => f.status === "done").length;
  const hasError = !!error;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`mt-4 rounded-xl border p-4 ${
        hasError
          ? "border-clai-error/20 bg-clai-error/5"
          : "border-emerald-400/20 bg-emerald-400/5"
      }`}
    >
      <div className="flex items-center gap-2 mb-3">
        {hasError ? (
          <XCircle className="w-4 h-4 text-clai-error" />
        ) : (
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
        )}
        <span className={`text-sm font-medium ${hasError ? "text-clai-error" : "text-emerald-300"}`}>
          {hasError ? "Pipeline completed with errors" : "Pipeline completed"}
        </span>
      </div>
      <div className="grid grid-cols-3 gap-3 text-center">
        <div>
          <p className="text-lg font-semibold text-clai-text">{messages.length}</p>
          <p className="text-[10px] text-clai-muted uppercase tracking-wider">Responses</p>
        </div>
        <div>
          <p className="text-lg font-semibold text-clai-text">{doneFiles}</p>
          <p className="text-[10px] text-clai-muted uppercase tracking-wider">Files</p>
        </div>
        <div>
          <p className="text-lg font-semibold text-clai-text">
            {totalTokens > 0 ? totalTokens.toLocaleString() : totalDuration > 0 ? `${totalDuration.toFixed(0)}s` : "--"}
          </p>
          <p className="text-[10px] text-clai-muted uppercase tracking-wider">
            {totalTokens > 0 ? "Tokens" : "Duration"}
          </p>
        </div>
      </div>
    </motion.div>
  );
}
