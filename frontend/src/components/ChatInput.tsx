"use client";

import { useRef, useState, useCallback, useEffect } from "react";
import {
  Send, Square, Paperclip, ChevronDown,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "../lib/cn";
import { PHASES, type PhaseId } from "../lib/constants";
import { getUserConfig } from "../lib/storage";
import { DirectoryPickerModal } from "./DirectoryPickerModal";

interface Props {
  isRunning: boolean;
  onSend: (
    requirement: string,
    opts: {
      projectName: string;
      workspaceDir: string;
      useGithub: boolean;
      selectedPhases: string[];
      selectedFiles: string[];
    },
  ) => void;
  onStop: () => void;
  initialPrompt?: string;
  initialPhases?: PhaseId[];
}

export function ChatInput({
  isRunning,
  onSend,
  onStop,
  initialPrompt,
  initialPhases,
}: Props) {
  const [value, setValue] = useState("");
  const [selectedPhases, setSelectedPhases] = useState<string[]>(
    PHASES.map((p) => p.id),
  );
  const [showConfig, setShowConfig] = useState(false);
  const [projectName, setProjectName] = useState("my-project");
  const [workspaceDir, setWorkspaceDir] = useState("");
  const [useGithub, setUseGithub] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [pickerOpen, setPickerOpen] = useState(false);
  const [configLoaded, setConfigLoaded] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Load persisted config on mount
  useEffect(() => {
    const cfg = getUserConfig();
    if (cfg.lastWorkspace) setWorkspaceDir(cfg.lastWorkspace);
    if (cfg.lastProjectName) setProjectName(cfg.lastProjectName);
    setConfigLoaded(true);
  }, []);

  // Auto-show config panel if workspace is empty (first time user)
  useEffect(() => {
    if (configLoaded && !workspaceDir) {
      setShowConfig(true);
    }
  }, [configLoaded, workspaceDir]);

  // Apply initial prompt/phases from WelcomeScreen card click
  useEffect(() => {
    if (initialPrompt !== undefined) {
      setValue(initialPrompt);
      textareaRef.current?.focus();
    }
  }, [initialPrompt]);

  useEffect(() => {
    if (initialPhases) setSelectedPhases([...initialPhases]);
  }, [initialPhases]);

  const autoResize = useCallback(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 160) + "px";
  }, []);

  const togglePhase = (id: string) => {
    setSelectedPhases((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id],
    );
  };

  const handleSend = () => {
    if (!value.trim() || isRunning || selectedPhases.length === 0) return;
    onSend(value.trim(), {
      projectName: projectName.trim() || "my-project",
      workspaceDir: workspaceDir.trim(),
      useGithub,
      selectedPhases,
      selectedFiles,
    });
    setValue("");
    setShowConfig(false);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <>
      <div className="flex-shrink-0 border-t border-clai-border bg-clai-surface/80 backdrop-blur-sm px-4 pb-4 pt-3">
        <div className="max-w-3xl mx-auto">
          {/* Main input row */}
          <div className="relative rounded-xl border border-clai-border bg-clai-card focus-within:border-clai-accent/40 transition-colors">
            <textarea
              ref={textareaRef}
              value={value}
              onChange={(e) => {
                setValue(e.target.value);
                autoResize();
              }}
              onKeyDown={handleKeyDown}
              placeholder="Describe what to build..."
              rows={1}
              disabled={isRunning}
              className="w-full resize-none bg-transparent px-4 pt-3 pb-10 text-sm text-clai-text placeholder:text-clai-muted/60 focus:outline-none disabled:opacity-50 font-sans"
            />
            {/* Bottom action bar inside the input */}
            <div className="absolute bottom-2 left-2 right-2 flex items-center justify-between">
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setPickerOpen(true)}
                  disabled={isRunning}
                  title="Attach files"
                  className="p-1.5 rounded-lg text-clai-muted hover:text-clai-text hover:bg-clai-surface transition-colors disabled:opacity-40"
                >
                  <Paperclip className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setShowConfig((v) => !v)}
                  disabled={isRunning}
                  title="Project settings"
                  className={cn(
                    "p-1.5 rounded-lg transition-colors disabled:opacity-40 flex items-center gap-1",
                    showConfig
                      ? "text-clai-accent bg-clai-accent/10"
                      : "text-clai-muted hover:text-clai-text hover:bg-clai-surface",
                  )}
                >
                  <ChevronDown className={cn("w-3.5 h-3.5 transition-transform", showConfig && "rotate-180")} />
                  <span className="text-[10px] hidden sm:inline">Config</span>
                </button>
                {workspaceDir && (
                  <span className="text-[10px] text-clai-muted ml-1 truncate max-w-[120px]" title={workspaceDir}>
                    {workspaceDir.split(/[\\/]/).pop()}
                  </span>
                )}
                {selectedFiles.length > 0 && (
                  <span className="text-[10px] text-clai-muted ml-1">
                    +{selectedFiles.length} file{selectedFiles.length > 1 ? "s" : ""}
                  </span>
                )}
              </div>
              <div>
                {isRunning ? (
                  <button
                    onClick={onStop}
                    className="flex items-center gap-1.5 rounded-lg bg-clai-error/10 border border-clai-error/20 px-3 py-1.5 text-xs font-medium text-clai-error hover:bg-clai-error/20 transition-colors"
                  >
                    <Square className="w-3 h-3" />
                    Stop
                  </button>
                ) : (
                  <button
                    onClick={handleSend}
                    disabled={!value.trim() || selectedPhases.length === 0}
                    className="flex items-center gap-1.5 rounded-lg bg-clai-accent px-3 py-1.5 text-xs font-medium text-clai-bg hover:bg-cyan-400 disabled:opacity-30 disabled:hover:bg-clai-accent transition-colors"
                  >
                    <Send className="w-3 h-3" />
                    Send
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Phase chips */}
          <div className="flex items-center gap-1.5 mt-2 flex-wrap">
            {PHASES.map((phase) => {
              const active = selectedPhases.includes(phase.id);
              return (
                <button
                  key={phase.id}
                  onClick={() => togglePhase(phase.id)}
                  disabled={isRunning}
                  title={phase.description}
                  className={cn(
                    "rounded-full px-3 py-1 text-[11px] font-medium border transition-colors disabled:opacity-50",
                    active
                      ? "border-clai-accent/40 bg-clai-accent/10 text-clai-accent"
                      : "border-clai-border bg-transparent text-clai-muted hover:border-clai-muted/40",
                  )}
                >
                  {phase.label}
                </button>
              );
            })}
            {selectedPhases.length === 0 && (
              <span className="text-[10px] text-clai-error ml-1">Select at least one phase</span>
            )}
          </div>

          {/* Expandable config panel */}
          <AnimatePresence>
            {showConfig && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="overflow-hidden"
              >
                <div className="mt-3 rounded-xl border border-clai-border bg-clai-surface/60 p-3 grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <label className="block text-[10px] uppercase tracking-widest text-clai-muted mb-1">
                      Project Name
                    </label>
                    <input
                      className="w-full rounded-lg border border-clai-border bg-clai-card px-3 py-1.5 text-xs text-clai-text placeholder:text-clai-muted/60 focus:outline-none focus:border-clai-accent/40"
                      value={projectName}
                      onChange={(e) => setProjectName(e.target.value)}
                      placeholder="my-project"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] uppercase tracking-widest text-clai-muted mb-1">
                      Workspace
                    </label>
                    <input
                      className="w-full rounded-lg border border-clai-border bg-clai-card px-3 py-1.5 text-xs text-clai-text placeholder:text-clai-muted/60 focus:outline-none focus:border-clai-accent/40"
                      value={workspaceDir}
                      onChange={(e) => setWorkspaceDir(e.target.value)}
                      placeholder="C:\path\to\workspace"
                    />
                  </div>
                  <div className="flex items-end">
                    <label className="flex items-center gap-2 text-xs text-clai-text cursor-pointer">
                      <input
                        type="checkbox"
                        checked={useGithub}
                        onChange={(e) => setUseGithub(e.target.checked)}
                        className="accent-clai-accent"
                      />
                      GitHub sync
                    </label>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
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
    </>
  );
}
