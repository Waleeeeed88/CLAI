"use client";
import { FileEntry } from "../lib/types";
import { AGENT_LABELS, AGENT_COLORS } from "./AgentBadge";

export function FilesPanel({ files }: { files: FileEntry[] }) {
  if (files.length === 0) {
    return (
      <div className="w-72 flex-shrink-0 border-l border-slate-800 bg-[#081021]">
        <div className="px-4 py-3 text-[10px] font-semibold text-slate-400 uppercase tracking-widest">
          File Activity
        </div>
        <div className="px-4 py-2 text-xs text-slate-500">
          File operations will appear here once tools start writing.
        </div>
      </div>
    );
  }

  const sorted = [...files].sort((a, b) => b.timestamp - a.timestamp);

  return (
    <div className="w-72 flex-shrink-0 border-l border-slate-800 bg-[#081021] overflow-y-auto">
      <div className="px-4 py-3 text-[10px] font-semibold text-slate-400 uppercase tracking-widest">
        Files ({files.length})
      </div>
      <div className="px-3 pb-3 space-y-1.5">
        {sorted.map((f) => {
          const nameParts = f.path.split(/[\\/]/g);
          const name = nameParts[nameParts.length - 1] ?? f.path;
          const color = AGENT_COLORS[f.agent] ?? "#666";
          const statusCls = f.status === "done"
            ? "text-emerald-300 border-emerald-700/40 bg-emerald-900/20"
            : f.status === "writing"
            ? "text-cyan-300 border-cyan-700/40 bg-cyan-900/20"
            : "text-red-300 border-red-700/40 bg-red-900/20";
          const parent = nameParts.length > 1 ? nameParts.slice(0, -1).join("/") : "";
          return (
            <div key={f.id} className="rounded border border-slate-800 bg-slate-900/70 p-2.5 text-[11px]">
              <div className="flex items-center gap-2">
                <span className={`rounded border px-1.5 py-0.5 text-[10px] font-semibold ${statusCls}`}>
                  {f.status === "writing" ? "writing" : f.status === "done" ? "done" : "error"}
                </span>
                <span className="text-[9px] font-bold ml-auto" style={{ color }}>
                  {AGENT_LABELS[f.agent] ?? f.agent}
                </span>
              </div>
              <div className="mt-1.5 truncate text-slate-100" title={f.path}>
                {name}
              </div>
              <div className="truncate text-[10px] text-slate-500" title={parent}>
                {parent || "root"}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
