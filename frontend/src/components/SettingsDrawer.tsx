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
            className="fixed inset-0 z-40 bg-black/72 backdrop-blur-sm"
          />
          <motion.aside
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 28, stiffness: 280 }}
            className="fixed inset-y-0 right-0 z-50 w-full max-w-[430px] overflow-y-auto border-l border-white/8 bg-clai-shell/96 shadow-[-24px_0_70px_rgba(0,0,0,0.45)] backdrop-blur-xl"
          >
            <div className="flex min-h-full flex-col">
              <div className="border-b border-white/6 px-5 py-5">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-clai-muted">
                      Settings
                    </p>
                    <h2 className="mt-2 text-2xl font-semibold tracking-tight text-clai-text">
                      Model Routing
                    </h2>
                    <p className="mt-1 text-sm text-clai-muted">
                      Adjust provider and model assignments for each CLAI role.
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

              <div className="flex-1 space-y-6 px-5 py-5">
                <section className="rounded-[28px] border border-white/8 bg-white/[0.035] p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <h3 className="text-[11px] font-semibold uppercase tracking-[0.22em] text-clai-muted">
                        Assignments
                      </h3>
                      <p className="mt-2 text-sm text-clai-muted">
                        Save updates when you finish editing the active role map.
                      </p>
                    </div>
                    <button
                      onClick={handleSave}
                      disabled={saving || loading}
                      className={cn(
                        "inline-flex items-center gap-2 rounded-2xl border px-4 py-2.5 text-sm font-semibold transition-all",
                        saved
                          ? "border-white/10 bg-white/[0.08] text-white"
                          : "border-white/10 bg-white text-clai-bg shadow-[0_12px_28px_rgba(0,0,0,0.28)] hover:bg-[#e8e8ea]",
                        (saving || loading) && "cursor-not-allowed opacity-60",
                      )}
                    >
                      {saving ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : saved ? (
                        <Check className="h-4 w-4" />
                      ) : (
                        <Save className="h-4 w-4" />
                      )}
                      {saved ? "Saved" : "Save"}
                    </button>
                  </div>

                  {error && (
                    <div className="mt-4 rounded-2xl border border-clai-error/20 bg-clai-error/10 px-4 py-3 text-sm text-clai-error">
                      {error}
                    </div>
                  )}

                  {loading ? (
                    <div className="flex items-center justify-center py-16">
                      <Loader2 className="h-6 w-6 animate-spin text-clai-muted" />
                    </div>
                  ) : (
                    <div className="mt-5 space-y-4">
                      {roles.map((role) => {
                        const agent = AGENTS[role];
                        const roleConfig = config[role];
                        if (!roleConfig) return null;

                        const modelSuggestions = DEFAULT_MODELS[roleConfig.provider] ?? [];

                        return (
                          <div
                            key={role}
                            className="rounded-[24px] border border-white/8 bg-black/15 p-4"
                          >
                            <div className="flex items-center gap-3">
                              <span
                                className="h-10 w-10 rounded-2xl border border-white/8"
                                style={{ backgroundColor: `${agent.color}18` }}
                              />
                              <div className="min-w-0">
                                <p className="text-sm font-semibold text-clai-text">
                                  {agent.label}
                                </p>
                                <p className="text-[11px] uppercase tracking-[0.18em] text-clai-muted">
                                  {role.replace(/_/g, " ")}
                                </p>
                              </div>
                            </div>

                            <div className="mt-4 grid gap-3">
                              <label className="block">
                                <span className="mb-1.5 block text-[10px] font-semibold uppercase tracking-[0.22em] text-clai-muted">
                                  Provider
                                </span>
                                <select
                                  value={roleConfig.provider}
                                  onChange={(e) => handleProviderChange(role, e.target.value)}
                                  className="w-full rounded-2xl border border-white/8 bg-white/[0.04] px-4 py-3 text-sm text-clai-text focus:border-white/15 focus:outline-none"
                                >
                                  {providers.map((provider) => {
                                    const meta = PROVIDERS.find((entry) => entry.id === provider);
                                    return (
                                      <option key={provider} value={provider}>
                                        {meta?.label ?? provider}
                                      </option>
                                    );
                                  })}
                                </select>
                              </label>

                              <label className="block">
                                <span className="mb-1.5 block text-[10px] font-semibold uppercase tracking-[0.22em] text-clai-muted">
                                  Model
                                </span>
                                <input
                                  type="text"
                                  list={`models-${role}`}
                                  value={roleConfig.model}
                                  onChange={(e) => handleModelChange(role, e.target.value)}
                                  className="w-full rounded-2xl border border-white/8 bg-white/[0.04] px-4 py-3 font-mono text-sm text-clai-text placeholder:text-clai-muted/65 focus:border-white/15 focus:outline-none"
                                  placeholder="model name"
                                />
                                <datalist id={`models-${role}`}>
                                  {modelSuggestions.map((model) => (
                                    <option key={model} value={model} />
                                  ))}
                                </datalist>
                              </label>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </section>

                <section className="rounded-[28px] border border-white/8 bg-white/[0.035] p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
                  <h3 className="text-[11px] font-semibold uppercase tracking-[0.22em] text-clai-muted">
                    Keyboard Shortcuts
                  </h3>
                  <div className="mt-4 space-y-2">
                    <Shortcut keys="Enter" action="Send message" />
                    <Shortcut keys="Shift + Enter" action="New line" />
                  </div>
                </section>
              </div>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}

function Shortcut({ keys, action }: { keys: string; action: string }) {
  return (
    <div className="flex items-center justify-between rounded-2xl border border-white/8 bg-black/15 px-4 py-3">
      <span className="text-sm text-clai-muted">{action}</span>
      <kbd className="rounded-xl border border-white/10 bg-white/[0.06] px-2.5 py-1 font-mono text-[11px] text-clai-text">
        {keys}
      </kbd>
    </div>
  );
}
