import { ChatMessage, PhaseEvent, FileEntry } from "./types";

const STORAGE_KEY = "clai_conversations";
const CONFIG_KEY = "clai_user_config";

export interface ConversationData {
  id: string;
  title: string;
  messages: ChatMessage[];
  phases: PhaseEvent[];
  files: FileEntry[];
  createdAt: number;
  updatedAt: number;
}

export interface ConversationSummary {
  id: string;
  title: string;
  messageCount: number;
  createdAt: number;
  updatedAt: number;
}

export interface UserConfig {
  lastWorkspace: string;
  lastProjectName: string;
}

// ── Conversations ──────────────────────────────────────────────

function getAll(): Record<string, ConversationData> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function setAll(data: Record<string, ConversationData>) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

export function saveConversation(
  id: string,
  messages: ChatMessage[],
  phases: PhaseEvent[],
  files: FileEntry[],
) {
  const all = getAll();
  const existing = all[id];
  const title =
    existing?.title ??
    generateTitle(messages) ??
    "Untitled";
  all[id] = {
    id,
    title,
    messages,
    phases,
    files,
    createdAt: existing?.createdAt ?? Date.now(),
    updatedAt: Date.now(),
  };
  setAll(all);
}

export function loadConversation(id: string): ConversationData | null {
  const all = getAll();
  return all[id] ?? null;
}

export function listConversations(): ConversationSummary[] {
  const all = getAll();
  return Object.values(all)
    .map((c) => ({
      id: c.id,
      title: c.title,
      messageCount: c.messages.length,
      createdAt: c.createdAt,
      updatedAt: c.updatedAt,
    }))
    .sort((a, b) => b.updatedAt - a.updatedAt);
}

export function deleteConversation(id: string) {
  const all = getAll();
  delete all[id];
  setAll(all);
}

function generateTitle(messages: ChatMessage[]): string | null {
  const first = messages.find((m) => m.content && !m.isStreaming);
  if (!first) return null;
  const text = first.content.replace(/[#*_`]/g, "").trim();
  return text.length > 60 ? text.slice(0, 57) + "..." : text;
}

// ── User Config ────────────────────────────────────────────────

export function getUserConfig(): UserConfig {
  try {
    const raw = localStorage.getItem(CONFIG_KEY);
    return raw ? JSON.parse(raw) : { lastWorkspace: "", lastProjectName: "my-project" };
  } catch {
    return { lastWorkspace: "", lastProjectName: "my-project" };
  }
}

export function saveUserConfig(config: Partial<UserConfig>) {
  const current = getUserConfig();
  localStorage.setItem(CONFIG_KEY, JSON.stringify({ ...current, ...config }));
}
