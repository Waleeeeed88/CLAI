import {
  FilesystemListResponse,
  FilesystemRootsResponse,
} from "./types";

const BASE = "http://localhost:8000/api";

export interface StartRunRequest {
  type: "stage" | "workflow" | "pipeline";
  stage?: string;
  workflow?: string;
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
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  const data = await res.json();
  return data.session_id as string;
}

export async function fetchWorkflows(): Promise<{
  workflows: string[];
  stages: string[];
  stage_details: Record<string, Record<string, string>>;
}> {
  const res = await fetch(`${BASE}/workflows`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export function getStreamUrl(sessionId: string): string {
  return `${BASE}/chat/${sessionId}/stream`;
}

export async function fetchFilesystemRoots(): Promise<FilesystemRootsResponse> {
  const res = await fetch(`${BASE}/filesystem/roots`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
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
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}
