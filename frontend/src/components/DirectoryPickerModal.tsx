"use client";

import { useEffect, useMemo, useState } from "react";
import { fetchFilesystemEntries, fetchFilesystemRoots } from "../lib/api";
import { FilesystemEntry } from "../lib/types";

interface Props {
  open: boolean;
  initialWorkspaceDir: string;
  initialSelectedFiles: string[];
  onClose: () => void;
  onApply: (workspaceDir: string, selectedFiles: string[]) => void;
}

interface ViewState {
  path: string;
  parent: string | null;
  entries: FilesystemEntry[];
}

export function DirectoryPickerModal({
  open,
  initialWorkspaceDir,
  initialSelectedFiles,
  onClose,
  onApply,
}: Props) {
  const [view, setView] = useState<ViewState | null>(null);
  const [currentPath, setCurrentPath] = useState<string>("");
  const [workspaceDir, setWorkspaceDir] = useState<string>(initialWorkspaceDir);
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(
    new Set(initialSelectedFiles),
  );
  const [pathInput, setPathInput] = useState(initialWorkspaceDir);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedCount = selectedFiles.size;

  useEffect(() => {
    if (!open) return;
    setWorkspaceDir(initialWorkspaceDir);
    setPathInput(initialWorkspaceDir);
    setSelectedFiles(new Set(initialSelectedFiles));
    setCurrentPath(initialWorkspaceDir);
  }, [open, initialWorkspaceDir, initialSelectedFiles]);

  useEffect(() => {
    if (!open) return;
    let canceled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        if (!currentPath) {
          const roots = await fetchFilesystemRoots();
          if (canceled) return;
          setView({
            path: "",
            parent: null,
            entries: roots.roots,
          });
        } else {
          const data = await fetchFilesystemEntries(currentPath, true);
          if (canceled) return;
          setView({
            path: data.path,
            parent: data.parent,
            entries: data.entries,
          });
          setPathInput(data.path);
        }
      } catch {
        if (!canceled) setError("Unable to load this location.");
      } finally {
        if (!canceled) setLoading(false);
      }
    };
    void load();
    return () => {
      canceled = true;
    };
  }, [open, currentPath]);

  const directories = useMemo(
    () => (view?.entries ?? []).filter((entry) => entry.type === "directory"),
    [view],
  );

  const files = useMemo(
    () => (view?.entries ?? []).filter((entry) => entry.type === "file"),
    [view],
  );

  if (!open) return null;

  const toggleFile = (filePath: string) => {
    setSelectedFiles((prev) => {
      const next = new Set(prev);
      if (next.has(filePath)) next.delete(filePath);
      else next.add(filePath);
      return next;
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-4xl rounded-2xl border border-slate-800 bg-[#0f172a] shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-800 px-5 py-3">
          <div>
            <h3 className="text-sm font-semibold text-slate-100">System Browser</h3>
            <p className="text-xs text-slate-400">Pick a workspace folder and optional input files</p>
          </div>
          <button
            onClick={onClose}
            className="rounded-md border border-slate-700 px-2 py-1 text-xs text-slate-300 hover:border-slate-500"
          >
            Close
          </button>
        </div>

        <div className="border-b border-slate-800 px-5 py-3">
          <div className="flex gap-2">
            <input
              className="flex-1 rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-slate-200 focus:border-cyan-500 focus:outline-none"
              value={pathInput}
              placeholder="Enter path (e.g. C:\\Users\\Walid\\Projects)"
              onChange={(e) => setPathInput(e.target.value)}
            />
            <button
              onClick={() => setCurrentPath(pathInput.trim())}
              className="rounded-md bg-cyan-600 px-3 py-2 text-xs font-semibold text-white hover:bg-cyan-500"
            >
              Go
            </button>
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
            <button
              onClick={() => setCurrentPath("")}
              className="rounded-md border border-slate-700 px-2 py-1 text-slate-300 hover:border-slate-500"
            >
              Roots
            </button>
            <button
              disabled={!view?.parent}
              onClick={() => view?.parent && setCurrentPath(view.parent)}
              className="rounded-md border border-slate-700 px-2 py-1 text-slate-300 disabled:opacity-40 hover:border-slate-500"
            >
              Up
            </button>
            {view?.path && (
              <button
                onClick={() => setWorkspaceDir(view.path)}
                className="rounded-md border border-emerald-700 px-2 py-1 text-emerald-300 hover:bg-emerald-900/30"
              >
                Use current folder
              </button>
            )}
            <span className="ml-auto text-slate-400">Selected files: {selectedCount}</span>
          </div>
        </div>

        <div className="grid gap-0 md:grid-cols-2">
          <div className="border-r border-slate-800 px-5 py-4">
            <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-300">Folders</h4>
            <div className="h-72 overflow-y-auto rounded-md border border-slate-800 bg-slate-950/60">
              {loading && <div className="p-3 text-xs text-slate-500">Loading...</div>}
              {!loading && error && <div className="p-3 text-xs text-red-400">{error}</div>}
              {!loading && !error && directories.length === 0 && (
                <div className="p-3 text-xs text-slate-500">No folders here.</div>
              )}
              {!loading &&
                !error &&
                directories.map((entry) => (
                  <div key={entry.path} className="flex items-center gap-2 border-b border-slate-900 px-2 py-1.5">
                    <button
                      onClick={() => setCurrentPath(entry.path)}
                      className="min-w-0 flex-1 truncate text-left text-xs text-slate-200 hover:text-cyan-300"
                      title={entry.path}
                    >
                      {entry.name}
                    </button>
                    <button
                      onClick={() => setWorkspaceDir(entry.path)}
                      className="rounded border border-slate-700 px-2 py-0.5 text-[10px] text-slate-300 hover:border-emerald-600 hover:text-emerald-300"
                    >
                      Use
                    </button>
                  </div>
                ))}
            </div>
          </div>

          <div className="px-5 py-4">
            <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-300">Files</h4>
            <div className="h-72 overflow-y-auto rounded-md border border-slate-800 bg-slate-950/60">
              {loading && <div className="p-3 text-xs text-slate-500">Loading...</div>}
              {!loading && error && <div className="p-3 text-xs text-red-400">{error}</div>}
              {!loading && !error && files.length === 0 && (
                <div className="p-3 text-xs text-slate-500">No files in this folder.</div>
              )}
              {!loading &&
                !error &&
                files.map((entry) => (
                  <label
                    key={entry.path}
                    className="flex cursor-pointer items-center gap-2 border-b border-slate-900 px-2 py-1.5 text-xs text-slate-300"
                  >
                    <input
                      type="checkbox"
                      checked={selectedFiles.has(entry.path)}
                      onChange={() => toggleFile(entry.path)}
                      className="accent-cyan-500"
                    />
                    <span className="truncate" title={entry.path}>
                      {entry.name}
                    </span>
                  </label>
                ))}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 border-t border-slate-800 px-5 py-3">
          <div className="min-w-0 flex-1">
            <div className="truncate text-xs text-slate-400">
              Workspace: {workspaceDir || "not selected"}
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-md border border-slate-700 px-3 py-1.5 text-xs text-slate-300 hover:border-slate-500"
          >
            Cancel
          </button>
          <button
            onClick={() => onApply(workspaceDir, Array.from(selectedFiles))}
            className="rounded-md bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-500"
          >
            Apply selection
          </button>
        </div>
      </div>
    </div>
  );
}
