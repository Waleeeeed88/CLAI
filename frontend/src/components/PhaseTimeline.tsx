"use client";

import { useEffect, useRef, useState } from "react";
import { Check, X, Loader2 } from "lucide-react";
import { cn } from "../lib/cn";
import { PhaseEvent } from "../lib/types";

function ElapsedTimer() {
  const [s, setS] = useState(0);
  const t0 = useRef(Date.now());
  useEffect(() => {
    const id = setInterval(
      () => setS(Math.floor((Date.now() - t0.current) / 1000)),
      1000,
    );
    return () => clearInterval(id);
  }, []);
  return <span className="font-mono tabular-nums text-[10px]">{s}s</span>;
}

interface Props {
  phases: PhaseEvent[];
}

export function PhaseTimeline({ phases }: Props) {
  if (phases.length === 0) return null;

  return (
    <div className="flex items-center justify-center gap-0 py-3 px-4 flex-wrap">
      {phases.map((p, i) => {
        const running = !p.status || p.status === "running";
        const failed = p.status === "failed";
        const done = p.status === "done" || p.status === "completed";
        const label = p.phase.replace(/_/g, " ");

        return (
          <div key={i} className="flex items-center">
            {i > 0 && (
              <div
                className={cn(
                  "w-8 sm:w-12 h-px mx-1",
                  done ? "bg-clai-success" : running ? "bg-clai-accent/40" : "bg-clai-border",
                )}
              />
            )}
            <div className="flex flex-col items-center gap-1">
              <div
                className={cn(
                  "w-7 h-7 rounded-full flex items-center justify-center border-2 transition-colors",
                  done && "border-clai-success bg-clai-success/10",
                  running && "border-clai-accent bg-clai-accent/10",
                  failed && "border-clai-error bg-clai-error/10",
                  !done && !running && !failed && "border-clai-border bg-clai-surface",
                )}
              >
                {done && <Check className="w-3.5 h-3.5 text-clai-success" />}
                {running && <Loader2 className="w-3.5 h-3.5 text-clai-accent animate-spin" />}
                {failed && <X className="w-3.5 h-3.5 text-clai-error" />}
              </div>
              <span
                className={cn(
                  "text-[10px] font-medium capitalize whitespace-nowrap",
                  done && "text-clai-success",
                  running && "text-clai-accent",
                  failed && "text-clai-error",
                  !done && !running && !failed && "text-clai-muted",
                )}
              >
                {label}
              </span>
              <span className="text-[10px] text-clai-muted">
                {running ? (
                  <ElapsedTimer />
                ) : p.duration != null ? (
                  <span className="font-mono tabular-nums">{p.duration.toFixed(1)}s</span>
                ) : null}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
