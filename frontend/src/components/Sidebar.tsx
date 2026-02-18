"use client";

import { useMemo, useState } from "react";
import { DirectoryPickerModal } from "./DirectoryPickerModal";

const SIMPLE_PHASES = [
  {
    id: "planning",
    label: "Planning",
    description: "Create plan, stories, and issue backlog.",
  },
  {
    id: "implementation",
    label: "Implementation",
    description: "Build code plus QA artifacts and Excel test plan.",
  },
  {
    id: "github_mcp",
    label: "GitHub MCP",
    description: "Sync issues to GitHub, or create local txt fallback.",
  },
] as const;

interface RunOptions {
  projectName: string;
  workspaceDir: string;
  useGithub: boolean;
  selectedPhases: string[];
  selectedFiles: string[];
}

interface Props {
  onStart: (requirement: string, runOptions: RunOptions) => void;
  isRunning: boolean;
  onReset: () => void;
  connectionError: boolean;
}

export function Sidebar({ onStart, isRunning, onReset, connectionError }: Props) {
  const [requirement, setRequirement] = useState("");
  const [projectName, setProjectName] = useState("my-project");
  const [workspaceDir, setWorkspaceDir] = useState("");
  const [useGithub, setUseGithub] = useState(true);
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [selectedPhases, setSelectedPhases] = useState<string[]>(
    SIMPLE_PHASES.map((p) => p.id),
  );
  const [pickerOpen, setPickerOpen] = useState(false);

  const phaseError = selectedPhases.length === 0;

  const selectedFilesPreview = useMemo(
    () => selectedFiles.slice(0, 4),
    [selectedFiles],
  );

  const togglePhase = (phase: string) => {
    setSelectedPhases((prev) =>
      prev.includes(phase) ? prev.filter((p) => p !== phase) : [...prev, phase],
    );
  };

  const run = () => {
    if (!requirement.trim() || phaseError) return;
    onStart(requirement.trim(), {
      projectName: projectName.trim() || "my-project",
      workspaceDir: workspaceDir.trim(),
      useGithub,
      selectedPhases,
      selectedFiles,
    });
  };

  return (
    <div className="w-full lg:w-80 flex-shrink-0 flex flex-col h-[52vh] lg:h-full bg-[#07101f] border-b lg:border-b-0 border-r-0 lg:border-r border-slate-800">
      <div className="px-4 py-3 border-b border-slate-800 bg-gradient-to-r from-cyan-500/10 to-emerald-500/10">
        <span className="font-semibold text-sm text-slate-100">CLAI Simple Flow</span>
        <span className="text-[10px] text-slate-400 ml-2">Plan / Implement / GitHub</span>
      </div>

      {connectionError && (
        <div className="mx-3 mt-2 text-[10px] text-red-300 bg-red-500/10 border border-red-500/20 rounded px-2 py-1.5">
          Backend offline
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">
          <div className="text-[10px] uppercase tracking-widest text-slate-400 mb-2">Phases</div>
          <div className="space-y-2">
            {SIMPLE_PHASES.map((phase) => (
              <label key={phase.id} className="flex items-start gap-2 text-[11px] text-slate-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={selectedPhases.includes(phase.id)}
                  onChange={() => togglePhase(phase.id)}
                  className="accent-emerald-500 mt-0.5"
                />
                <span className="min-w-0">
                  <span className="block text-slate-100 font-medium">{phase.label}</span>
                  <span className="block text-slate-400">{phase.description}</span>
                </span>
              </label>
            ))}
          </div>
          {phaseError && (
            <div className="mt-2 text-[10px] text-red-300">Select at least one phase.</div>
          )}
        </div>

        <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3 space-y-2">
          <div className="text-[10px] uppercase tracking-widest text-slate-400">Project</div>
          <input
            className="w-full rounded border border-slate-700 bg-slate-900 px-2 py-1.5 text-[11px] text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500"
            placeholder="Project name"
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
          />
          <label className="flex items-center gap-1.5 text-[11px] text-slate-300 cursor-pointer">
            <input
              type="checkbox"
              checked={useGithub}
              onChange={(e) => setUseGithub(e.target.checked)}
              className="accent-cyan-500"
            />
            Enable GitHub MCP for issue sync
          </label>
        </div>

        <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3 space-y-2">
          <div className="text-[10px] uppercase tracking-widest text-slate-400">Workspace + Files</div>
          <input
            className="w-full rounded border border-slate-700 bg-slate-900 px-2 py-1.5 text-[11px] text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500"
            placeholder="Workspace directory"
            value={workspaceDir}
            onChange={(e) => setWorkspaceDir(e.target.value)}
          />
          <button
            type="button"
            disabled={isRunning}
            onClick={() => setPickerOpen(true)}
            className="w-full rounded border border-cyan-700 px-2 py-1.5 text-[11px] text-cyan-300 hover:bg-cyan-900/20 disabled:opacity-50"
          >
            Browse files/folders
          </button>
          {selectedFiles.length > 0 && (
            <div className="rounded border border-slate-800 bg-slate-950/60 p-2">
              <div className="mb-1 text-[10px] uppercase tracking-widest text-slate-500">Selected files</div>
              <div className="space-y-1">
                {selectedFilesPreview.map((filePath) => (
                  <div key={filePath} className="truncate text-[11px] text-slate-300" title={filePath}>
                    {filePath}
                  </div>
                ))}
              </div>
              {selectedFiles.length > 4 && (
                <div className="mt-1 text-[10px] text-slate-500">
                  +{selectedFiles.length - 4} more
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="p-3 border-t border-slate-800 space-y-2 bg-slate-900/60">
        <textarea
          className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-2 text-[12px] text-slate-100 placeholder:text-slate-500 resize-none focus:outline-none focus:border-cyan-500"
          rows={4}
          placeholder="Describe what to build..."
          value={requirement}
          onChange={(e) => setRequirement(e.target.value)}
        />
        <button
          disabled={isRunning || !requirement.trim() || phaseError}
          onClick={run}
          className="w-full bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-800 disabled:text-slate-500 text-white text-[12px] font-semibold rounded py-1.5 transition-colors"
        >
          {isRunning ? "Running..." : "Run Simple Flow"}
        </button>
        {!isRunning && (
          <button
            onClick={() => {
              onReset();
              setRequirement("");
              setProjectName("my-project");
              setWorkspaceDir("");
              setUseGithub(true);
              setSelectedFiles([]);
              setSelectedPhases(SIMPLE_PHASES.map((p) => p.id));
            }}
            className="w-full text-[11px] text-slate-500 hover:text-slate-300 transition-colors"
          >
            Clear
          </button>
        )}
      </div>

      <DirectoryPickerModal
        open={pickerOpen}
        initialWorkspaceDir={workspaceDir}
        initialSelectedFiles={selectedFiles}
        onClose={() => setPickerOpen(false)}
        onApply={(dir, files) => {
          setWorkspaceDir(dir);
          setSelectedFiles(files);
          setPickerOpen(false);
        }}
      />
    </div>
  );
}
