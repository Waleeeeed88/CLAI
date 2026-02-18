"use client";
import { useState } from "react";
import { ToolCallRecord } from "../lib/types";

export function ToolCallBlock({ toolCall }: { toolCall: ToolCallRecord }) {
  const [open, setOpen] = useState(false);
  const isDone = toolCall.result !== undefined;

  return (
    <div className="my-1 rounded border border-[#16162a] bg-[#0d0d16] text-[11px] font-mono overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2 px-2.5 py-1.5 hover:bg-white/[0.02] text-left"
      >
        <span className="text-[#505070]">{toolCall.tool}</span>
        <span className="ml-auto">
          {!isDone && <span className="text-blue-400 animate-pulse">...</span>}
          {isDone && toolCall.success && <span className="text-emerald-400">ok</span>}
          {isDone && !toolCall.success && <span className="text-red-400">err</span>}
        </span>
      </button>
      {open && (
        <div className="px-2.5 pb-2 pt-1 border-t border-[#16162a] text-[10px] text-[#404060] space-y-0.5">
          {Object.entries(toolCall.args).map(([k, v]) => (
            <div key={k}><span className="text-[#353550]">{k}:</span> {String(v)}</div>
          ))}
          {toolCall.result && (
            <div className="mt-1 pt-1 border-t border-[#12122a] text-[#353550] break-all">{toolCall.result}</div>
          )}
        </div>
      )}
    </div>
  );
}
