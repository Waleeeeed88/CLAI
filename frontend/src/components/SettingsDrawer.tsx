"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Save, Loader2, Check } from "lucide-react";
import { cn } from "../lib/cn";
import { AGENTS, PROVIDERS, DEFAULT_MODELS, type AgentRole } from "../lib/constants";
import {
  fetchModelConfig,
  updateModelConfig,
  type RoleConfig,
} from "../lib/api";

interface Props {
  open: boolean;
  onClose: () => void;
}

type RoleOverrides = Record<string, RoleConfig>;

export function SettingsDrawer({ open, onClose }: Props) {
  const [config, setConfig] = useState<RoleOverrides>({});
  const [providers, setProviders] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    setError(null);
    setSaved(false);
    fetchModelConfig()
      .then((res) => {
        setConfig(res.roles);
        setProviders(res.providers);
      })
      .catch(() => setError("Failed to load config"))
      .finally(() => setLoading(false));
  }, [open]);

  const handleProviderChange = (role: string, provider: string) => {
    setConfig((prev) => ({
      ...prev,
      [role]: {
        ...prev[role],
        provider,
        // Auto-fill first default model for the new provider
        model: DEFAULT_MODELS[provider]?.[0] ?? prev[role]?.model ?? "",
      },
    }));
    setSaved(false);
  };

  const handleModelChange = (role: string, model: string) => {
    setConfig((prev) => ({
      ...prev,
      [role]: { ...prev[role], model },
    }));
    setSaved(false);
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      const res = await updateModelConfig(config);
      setConfig(res.roles);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {
      setError("Failed to save config");
    } finally {
      setSaving(false);
    }
  };

  const roles = Object.keys(AGENTS) as AgentRole[];

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-40 bg-black/30"
          />
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 30, stiffness: 300 }}
            className="fixed right-0 top-0 bottom-0 z-50 w-96 border-l border-clai-border bg-clai-bg overflow-y-auto"
          >
            <div className="flex items-center justify-between px-4 py-3 border-b border-clai-border">
              <span className="text-xs font-semibold text-clai-text uppercase tracking-widest">
                Settings
              </span>
              <button onClick={onClose} className="p-1 rounded text-clai-muted hover:text-clai-text transition-colors">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-4 space-y-6">
              {/* Model Configuration */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-[10px] uppercase tracking-widest text-clai-muted">
                    Model Assignments
                  </h4>
                  <button
                    onClick={handleSave}
                    disabled={saving || loading}
                    className={cn(
                      "flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[11px] font-medium transition-colors",
                      saved
                        ? "bg-clai-success/10 text-clai-success border border-clai-success/20"
                        : "bg-clai-accent/10 text-clai-accent border border-clai-accent/20 hover:bg-clai-accent/20",
                      (saving || loading) && "opacity-50 cursor-not-allowed",
                    )}
                  >
                    {saving ? (
                      <Loader2 className="w-3 h-3 animate-spin" />
                    ) : saved ? (
                      <Check className="w-3 h-3" />
                    ) : (
                      <Save className="w-3 h-3" />
                    )}
                    {saved ? "Saved" : "Save"}
                  </button>
                </div>

                {error && (
                  <p className="text-[11px] text-clai-error mb-3">{error}</p>
                )}

                {loading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-5 h-5 animate-spin text-clai-muted" />
                  </div>
                ) : (
                  <div className="space-y-4">
                    {roles.map((role) => {
                      const agent = AGENTS[role];
                      const roleConfig = config[role];
                      if (!roleConfig) return null;

                      const modelSuggestions =
                        DEFAULT_MODELS[roleConfig.provider] ?? [];

                      return (
                        <div
                          key={role}
                          className="rounded-xl border border-clai-border bg-clai-surface/40 p-3"
                        >
                          {/* Role header */}
                          <div className="flex items-center gap-2 mb-2.5">
                            <span
                              className="w-2 h-2 rounded-full flex-shrink-0"
                              style={{ backgroundColor: agent.color }}
                            />
                            <span className="text-xs font-medium text-clai-text">
                              {agent.label}
                            </span>
                          </div>

                          {/* Provider dropdown */}
                          <label className="block text-[10px] uppercase tracking-widest text-clai-muted mb-1">
                            Provider
                          </label>
                          <select
                            value={roleConfig.provider}
                            onChange={(e) =>
                              handleProviderChange(role, e.target.value)
                            }
                            className="w-full rounded-lg border border-clai-border bg-clai-card px-3 py-1.5 text-xs text-clai-text focus:outline-none focus:border-clai-accent/40 mb-2"
                          >
                            {providers.map((p) => {
                              const meta = PROVIDERS.find((pr) => pr.id === p);
                              return (
                                <option key={p} value={p}>
                                  {meta?.label ?? p}
                                </option>
                              );
                            })}
                          </select>

                          {/* Model input with datalist suggestions */}
                          <label className="block text-[10px] uppercase tracking-widest text-clai-muted mb-1">
                            Model
                          </label>
                          <input
                            type="text"
                            list={`models-${role}`}
                            value={roleConfig.model}
                            onChange={(e) =>
                              handleModelChange(role, e.target.value)
                            }
                            className="w-full rounded-lg border border-clai-border bg-clai-card px-3 py-1.5 text-xs text-clai-text placeholder:text-clai-muted/60 focus:outline-none focus:border-clai-accent/40 font-mono"
                            placeholder="model name"
                          />
                          <datalist id={`models-${role}`}>
                            {modelSuggestions.map((m) => (
                              <option key={m} value={m} />
                            ))}
                          </datalist>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Keyboard Shortcuts */}
              <div>
                <h4 className="text-[10px] uppercase tracking-widest text-clai-muted mb-3">
                  Keyboard Shortcuts
                </h4>
                <div className="space-y-1.5 text-xs">
                  <Shortcut keys="Enter" action="Send message" />
                  <Shortcut keys="Shift + Enter" action="New line" />
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

function Shortcut({ keys, action }: { keys: string; action: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-clai-muted">{action}</span>
      <kbd className="rounded border border-clai-border bg-clai-surface px-1.5 py-0.5 text-[10px] font-mono text-clai-text">
        {keys}
      </kbd>
    </div>
  );
}
