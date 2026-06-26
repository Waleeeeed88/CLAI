export const AGENTS = {
  senior_dev: { label: "Senior Architect", color: "#d7dce5", icon: "Crown" as const },
  coder: { label: "Coder", color: "#c6cfde", icon: "Code2" as const },
  coder_2: { label: "Coder 2", color: "#b5c0d1", icon: "Braces" as const },
  coder_3: { label: "Coder 3", color: "#a7b1c1", icon: "Sparkles" as const },
  qa: { label: "QA", color: "#d0d6df", icon: "TestTube2" as const },
  ba: { label: "Analyst", color: "#bfc4cd", icon: "FileSearch" as const },
  reviewer: { label: "Reviewer", color: "#e1e4ea", icon: "Eye" as const },
} as const;

export type AgentRole = keyof typeof AGENTS;

export const PHASES = [
  { id: 'planning',       label: 'Planning',       description: 'Create plan, stories, and issue backlog' },
  { id: 'implementation', label: 'Implementation',  description: 'Build code plus QA artifacts' },
  { id: 'github_mcp',     label: 'GitHub Sync',     description: 'Sync issues and code to GitHub' },
] as const;

export type PhaseId = typeof PHASES[number]['id'];

export const PROVIDERS = [
  { id: 'anthropic', label: 'Anthropic (Claude)' },
  { id: 'openai',    label: 'OpenAI (GPT)' },
  { id: 'google',    label: 'Google (Gemini)' },
  { id: 'kimi',      label: 'Kimi (Moonshot)' },
  { id: 'openrouter', label: 'OpenRouter' },
] as const;

export const DEFAULT_MODELS: Record<string, string[]> = {
  anthropic: ['claude-opus-4-8', 'claude-sonnet-4-6'],
  openai:    ['gpt-5.5', 'gpt-5.4', 'gpt-5.4-mini'],
  google:    ['gemini-3.1-pro-preview', 'gemini-3.5-flash', 'gemini-3.1-flash-preview'],
  kimi:      ['kimi-k2-thinking', 'kimi-k2-thinking-turbo', 'kimi-k2-0520'],
  openrouter: [
    '~anthropic/claude-opus-latest',
    '~anthropic/claude-sonnet-latest',
    '~qwen/qwen3-coder-latest',
    'openai/gpt-5.5',
    'google/gemini-3.1-pro',
  ],
};

export const SUGGESTION_CARDS = [
  {
    id: 'new-project',
    title: 'New Project',
    description: 'Start from a requirement and build end-to-end',
    phases: ['planning', 'implementation'] as PhaseId[],
    prompt: 'Build a project that ',
  },
  {
    id: 'code-review',
    title: 'Code Review',
    description: 'Analyze existing code for quality and issues',
    phases: ['planning'] as PhaseId[],
    prompt: 'Review the following codebase and provide detailed feedback: ',
  },
  {
    id: 'architecture',
    title: 'Architecture',
    description: 'Design a system from scratch',
    phases: ['planning'] as PhaseId[],
    prompt: 'Design the architecture for: ',
  },
  {
    id: 'testing',
    title: 'Testing',
    description: 'Generate test plans and run QA',
    phases: ['planning', 'implementation'] as PhaseId[],
    prompt: 'Create a comprehensive test plan for: ',
  },
  {
    id: 'github-sync',
    title: 'GitHub Sync',
    description: 'Push issues, PRs, and code to GitHub',
    phases: ['planning', 'implementation', 'github_mcp'] as PhaseId[],
    prompt: 'Sync the following project to GitHub with issues and tracking: ',
  },
] as const;
