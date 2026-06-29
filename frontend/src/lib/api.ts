import {
  FilesystemListResponse,
  FilesystemRootsResponse,
} from "./types";

const BASE = "http://localhost:8000/api";

async function raiseApiError(res: Response): Promise<never> {
  let message = `API error: ${res.status}`;
  try {
    const data = await res.json();
    if (typeof data?.detail === "string") message = data.detail;
  } catch {
    // Keep the status-only fallback when the server does not return JSON.
  }
  throw new Error(message);
}

export interface StartRunRequest {
  type: "pipeline";
  context?: Record<string, string>;
  requirement?: string;
  project_name?: string;
  workspace_dir?: string;
  selected_files?: string[];
  use_github?: boolean;
  selected_phases?: string[];
}

export async function startRun(req: StartRunRequest): Promise<string> {
  const res = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) await raiseApiError(res);
  const data = await res.json();
  return data.session_id as string;
}

export async function fetchWorkflows(): Promise<{
  workflows: string[];
  stages: string[];
  stage_details: Record<string, Record<string, string>>;
}> {
  const res = await fetch(`${BASE}/workflows`);
  if (!res.ok) await raiseApiError(res);
  return res.json();
}

export async function cancelRun(sessionId: string): Promise<void> {
  await fetch(`${BASE}/chat/${sessionId}/cancel`, { method: "POST" });
}

export function getStreamUrl(sessionId: string): string {
  return `${BASE}/chat/${sessionId}/stream`;
}

// Model config

export interface RoleConfig {
  provider: string;
  model: string;
}

export interface TeamPreset {
  id: string;
  label: string;
  description: string;
  roles: Record<string, RoleConfig>;
}

export interface ToolConfig {
  filesystem: boolean;
  scratchpad: boolean;
  enterprise_data: boolean;
  qa_tools: boolean;
  github_mcp: boolean;
}

export interface CostSavingConfig {
  enabled: boolean;
  max_output_tokens: number;
  history_messages: number;
  history_char_limit: number;
}

export interface ModelConfigResponse {
  roles: Record<string, RoleConfig>;
  providers: string[];
  presets: TeamPreset[];
  active_preset: string | null;
  tools: ToolConfig;
  cost_saving: CostSavingConfig;
  warnings: string[];
}

export async function fetchModelConfig(): Promise<ModelConfigResponse> {
  const res = await fetch(`${BASE}/config/models`);
  if (!res.ok) await raiseApiError(res);
  return res.json();
}

export async function updateModelConfig(
  overrides: Record<string, RoleConfig>,
  tools?: ToolConfig,
  costSaving?: CostSavingConfig,
  teamPreset?: string | null,
): Promise<ModelConfigResponse> {
  const res = await fetch(`${BASE}/config/models`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ overrides, tools, cost_saving: costSaving, team_preset: teamPreset }),
  });
  if (!res.ok) await raiseApiError(res);
  return res.json();
}

// Filesystem

export async function fetchFilesystemRoots(): Promise<FilesystemRootsResponse> {
  const res = await fetch(`${BASE}/filesystem/roots`);
  if (!res.ok) await raiseApiError(res);
  return res.json();
}

export async function fetchFilesystemEntries(
  path: string,
  includeFiles = true,
): Promise<FilesystemListResponse> {
  const params = new URLSearchParams({
    path,
    include_files: includeFiles ? "true" : "false",
  });
  const res = await fetch(`${BASE}/filesystem/list?${params.toString()}`);
  if (!res.ok) await raiseApiError(res);
  return res.json();
}
