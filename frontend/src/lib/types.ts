export type SSEEventType =
  | "agent_start"
  | "agent_done"
  | "tool_call"
  | "tool_result"
  | "phase_start"
  | "phase_done"
  | "stage_complete"
  | "workflow_complete"
  | "pipeline_complete"
  | "error"
  | "done";

export interface SSEEvent {
  type: SSEEventType;
  agent?: string;
  tool?: string;
  args?: Record<string, string>;
  preview?: string;
  content?: string;
  tokens?: number;
  model?: string;
  phase?: string;
  stage?: string;
  workflow?: string;
  context?: string;
  status?: string;
  steps?: number;
  duration?: number;
  message?: string;
  success?: boolean;
}

export interface ToolCallRecord {
  tool: string;
  args: Record<string, string>;
  result?: string;
  success?: boolean;
}

export interface ChatMessage {
  id: string;
  agent: string;
  content: string;
  tokens?: number;
  model?: string;
  toolCalls: ToolCallRecord[];
  isStreaming: boolean;
}

export interface PhaseEvent {
  phase: string;
  status?: string;
  duration?: number;
}

export type FileStatus = "writing" | "done" | "error";

export interface FileEntry {
  id: string;
  path: string;
  agent: string;
  tool: "write_file" | "append_file" | "delete_file";
  status: FileStatus;
  timestamp: number;
}

export interface FilesystemEntry {
  name: string;
  path: string;
  type: "directory" | "file";
  relative?: string;
}

export interface FilesystemRootsResponse {
  roots: FilesystemEntry[];
}

export interface FilesystemListResponse {
  path: string;
  name: string;
  parent: string | null;
  entries: FilesystemEntry[];
}
