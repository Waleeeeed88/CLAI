"use client";

import { type ReactNode, useEffect, useMemo, useState } from "react";
import { Check, ChevronUp, Folder, FolderTree, Search, X } from "lucide-react";
import { fetchFilesystemEntries, fetchFilesystemRoots } from "../lib/api";
import { cn } from "../lib/cn";
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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/74 p-4 backdrop-blur-sm">
      <div className="max-h-[90vh] w-full max-w-5xl overflow-hidden rounded-[32px] border border-white/10 bg-clai-shell/96 shadow-[0_30px_80px_rgba(0,0,0,0.45)]">
        <div className="border-b border-white/6 px-5 py-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-clai-muted">
                System Browser
              </p>
              <h3 className="mt-2 text-2xl font-semibold tracking-tight text-clai-text">
                Workspace and Files
              </h3>
              <p className="mt-1 text-sm text-clai-muted">
                Pick a working directory and optionally include files as run context.
              </p>
            </div>
            <button
              onClick={onClose}
              className="rounded-2xl border border-white/10 bg-white/[0.04] p-2 text-clai-muted transition-colors hover:border-white/15 hover:text-clai-text"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        <div className="border-b border-white/6 px-5 py-4">
          <div className="flex flex-col gap-3 lg:flex-row">
            <div className="relative min-w-0 flex-1">
              <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-clai-muted" />
              <input
                className="w-full rounded-2xl border border-white/8 bg-white/[0.04] py-3 pl-11 pr-4 text-sm text-clai-text placeholder:text-clai-muted/70 focus:border-white/15 focus:outline-none"
                value={pathInput}
                placeholder="Enter path (e.g. C:\\Users\\Walid\\Projects)"
                onChange={(e) => setPathInput(e.target.value)}
              />
            </div>
            <button
              onClick={() => setCurrentPath(pathInput.trim())}
              className="rounded-2xl bg-white px-5 py-3 text-sm font-semibold text-clai-bg shadow-[0_12px_28px_rgba(0,0,0,0.28)] transition hover:bg-[#e8e8ea]"
            >
              Go
            </button>
          </div>

          <div className="mt-3 flex flex-wrap items-center gap-2">
            <button
              onClick={() => setCurrentPath("")}
              className="rounded-2xl border border-white/10 bg-white/[0.04] px-3 py-2 text-xs font-medium text-clai-text transition-colors hover:border-white/15"
            >
              Roots
            </button>
            <button
              disabled={!view?.parent}
              onClick={() => view?.parent && setCurrentPath(view.parent)}
              className="inline-flex items-center gap-2 rounded-2xl border border-white/10 bg-white/[0.04] px-3 py-2 text-xs font-medium text-clai-text transition-colors hover:border-white/15 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <ChevronUp className="h-3.5 w-3.5" />
              Up
            </button>
            {view?.path && (
              <button
                onClick={() => setWorkspaceDir(view.path)}
                className="rounded-2xl border border-white/10 bg-white/[0.04] px-3 py-2 text-xs font-medium text-clai-text transition-colors hover:border-white/15"
              >
                Use current folder
              </button>
            )}
            <span className="ml-auto rounded-full border border-white/8 bg-black/15 px-3 py-1.5 text-xs text-clai-muted">
              Selected files: {selectedCount}
            </span>
          </div>
        </div>

        <div className="grid gap-0 lg:grid-cols-2">
          <section className="border-b border-white/6 px-5 py-4 lg:border-b-0 lg:border-r">
            <div className="mb-3 flex items-center gap-2">
              <span className="flex h-9 w-9 items-center justify-center rounded-2xl bg-white/[0.05] text-clai-text">
                <FolderTree className="h-4 w-4" />
              </span>
              <div>
                <h4 className="text-sm font-semibold text-clai-text">Folders</h4>
                <p className="text-xs text-clai-muted">Navigate to the workspace root.</p>
              </div>
            </div>
            <div className="h-72 overflow-y-auto rounded-[24px] border border-white/8 bg-black/15">
              {loading && <StateRow tone="muted">Loading...</StateRow>}
              {!loading && error && <StateRow tone="error">{error}</StateRow>}
              {!loading && !error && directories.length === 0 && (
                <StateRow tone="muted">No folders here.</StateRow>
              )}
              {!loading &&
                !error &&
                directories.map((entry) => (
                  <div
                    key={entry.path}
                    className="flex items-center gap-3 border-b border-white/6 px-3 py-3 last:border-b-0"
                  >
                    <button
                      onClick={() => setCurrentPath(entry.path)}
                      className="flex min-w-0 flex-1 items-center gap-3 text-left"
                      title={entry.path}
                    >
                      <span className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-2xl bg-white/[0.05] text-clai-text">
                        <Folder className="h-4 w-4" />
                      </span>
                      <span className="min-w-0 truncate text-sm text-clai-text transition-colors hover:text-white">
                        {entry.name}
                      </span>
                    </button>
                    <button
                      onClick={() => setWorkspaceDir(entry.path)}
                      className={cn(
                        "rounded-2xl border px-3 py-1.5 text-xs font-medium transition-colors",
                        workspaceDir === entry.path
                          ? "border-white/12 bg-white/[0.08] text-white"
                          : "border-white/10 bg-white/[0.04] text-clai-text hover:border-white/15",
                      )}
                    >
                      Use
                    </button>
                  </div>
                ))}
            </div>
          </section>

          <section className="px-5 py-4">
            <div className="mb-3 flex items-center gap-2">
              <span className="flex h-9 w-9 items-center justify-center rounded-2xl bg-white/[0.05] text-clai-text">
                <Check className="h-4 w-4" />
              </span>
              <div>
                <h4 className="text-sm font-semibold text-clai-text">Files</h4>
                <p className="text-xs text-clai-muted">Select files to pass into the run context.</p>
              </div>
            </div>
            <div className="h-72 overflow-y-auto rounded-[24px] border border-white/8 bg-black/15">
              {loading && <StateRow tone="muted">Loading...</StateRow>}
              {!loading && error && <StateRow tone="error">{error}</StateRow>}
              {!loading && !error && files.length === 0 && (
                <StateRow tone="muted">No files in this folder.</StateRow>
              )}
              {!loading &&
                !error &&
                files.map((entry) => (
                  <label
                    key={entry.path}
                    className="flex cursor-pointer items-center gap-3 border-b border-white/6 px-3 py-3 last:border-b-0"
                  >
                    <input
                      type="checkbox"
                      checked={selectedFiles.has(entry.path)}
                      onChange={() => toggleFile(entry.path)}
                      className="h-4 w-4 rounded border-white/20 bg-transparent accent-white"
                    />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm text-clai-text" title={entry.path}>
                        {entry.name}
                      </p>
                      <p className="truncate text-[11px] text-clai-muted" title={entry.path}>
                        {entry.path}
                      </p>
                    </div>
                  </label>
                ))}
            </div>
          </section>
        </div>

        <div className="flex flex-col gap-3 border-t border-white/6 px-5 py-4 sm:flex-row sm:items-center">
          <div className="min-w-0 flex-1 rounded-[22px] border border-white/8 bg-black/15 px-4 py-3">
            <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-clai-muted">
              Workspace
            </p>
            <p className="mt-1 truncate text-sm text-clai-text">
              {workspaceDir || "Not selected"}
            </p>
          </div>
          <div className="flex items-center gap-2 self-end sm:self-auto">
            <button
              onClick={onClose}
              className="rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm font-medium text-clai-text transition-colors hover:border-white/15"
            >
              Cancel
            </button>
            <button
              onClick={() => onApply(workspaceDir, Array.from(selectedFiles))}
              className="rounded-2xl bg-white px-4 py-3 text-sm font-semibold text-clai-bg shadow-[0_12px_28px_rgba(0,0,0,0.28)] transition hover:bg-[#e8e8ea]"
            >
              Apply selection
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function StateRow({
  children,
  tone,
}: {
  children: ReactNode;
  tone: "muted" | "error";
}) {
  return (
    <div
      className={cn(
        "px-4 py-4 text-sm",
        tone === "muted" ? "text-clai-muted" : "text-clai-error",
      )}
    >
      {children}
    </div>
  );
}
