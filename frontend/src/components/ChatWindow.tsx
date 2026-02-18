"use client";
import { useEffect, useRef, useState } from "react";
import { ChatMessage, PhaseEvent } from "../lib/types";
import { MessageBubble } from "./MessageBubble";

function ElapsedTimer() {
  const [s, setS] = useState(0);
  const t0 = useRef(Date.now());
  useEffect(() => {
    const id = setInterval(() => setS(Math.floor((Date.now() - t0.current) / 1000)), 1000);
    return () => clearInterval(id);
  }, []);
  return <span className="font-mono tabular-nums">{s}s</span>;
}

function PhaseBar({ event }: { event: PhaseEvent }) {
  const running = !event.status || event.status === "running";
  const failed = event.status === "failed";
  const cls = failed ? "text-red-400" : running ? "text-blue-400" : "text-emerald-400";

  return (
    <div className={`flex items-center gap-2 text-[11px] py-1 ${cls}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${running ? "animate-pulse" : ""}`}
        style={{ backgroundColor: "currentColor" }} />
      <span className="capitalize">{event.phase.replace(/_/g, " ")}</span>
      <span className="text-[10px] opacity-50 ml-auto">
        {running ? <ElapsedTimer /> : event.duration != null ? `${event.duration.toFixed(1)}s` : ""}
      </span>
    </div>
  );
}

interface Props {
  messages: ChatMessage[];
  phases: PhaseEvent[];
  isRunning: boolean;
  error: string | null;
}

export function ChatWindow({ messages, phases, isRunning, error }: Props) {
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
    <div ref={scrollRef} onScroll={onScroll} className="flex-1 overflow-y-auto px-6 py-4 bg-[radial-gradient(circle_at_top,#10203f_0%,#0b1224_38%,#070c19_100%)]">
      {empty && (
        <div className="flex h-full flex-col items-center justify-center text-center select-none">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 px-5 py-4">
            <div className="text-sm text-slate-300">Configure the 3-phase flow on the left</div>
            <div className="mt-1 text-xs text-slate-500">
              Then add your requirement and run.
            </div>
          </div>
        </div>
      )}

      {phases.length > 0 && (
        <div className="mb-3 rounded-lg border border-slate-800 bg-slate-900/50 px-3 py-2">
          {phases.map((p, i) => <PhaseBar key={i} event={p} />)}
        </div>
      )}

      {messages.map((msg) => <MessageBubble key={msg.id} message={msg} />)}

      {error && (
        <div className="mt-3 text-red-400 text-[12px] bg-red-500/5 border border-red-500/10 rounded px-3 py-2">
          {error}
        </div>
      )}

      <div ref={endRef} className="h-2" />
    </div>
  );
}
