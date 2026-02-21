export const AGENTS = {
  senior_dev: { label: 'Senior Dev', color: '#a78bfa', icon: 'Crown' as const },
  coder:      { label: 'Coder',      color: '#60a5fa', icon: 'Code2' as const },
  coder_2:    { label: 'Coder 2',    color: '#22d3ee', icon: 'Braces' as const },
  qa:         { label: 'QA',         color: '#34d399', icon: 'TestTube2' as const },
  ba:         { label: 'Analyst',    color: '#fbbf24', icon: 'FileSearch' as const },
  reviewer:   { label: 'Reviewer',   color: '#fb7185', icon: 'Eye' as const },
} as const;

export type AgentRole = keyof typeof AGENTS;

export const PHASES = [
  { id: 'planning',       label: 'Planning',       description: 'Create plan, stories, and issue backlog' },
  { id: 'implementation', label: 'Implementation',  description: 'Build code plus QA artifacts' },
  { id: 'github_mcp',     label: 'GitHub Sync',     description: 'Sync issues and code to GitHub' },
] as const;

export type PhaseId = typeof PHASES[number]['id'];

export const SUGGESTION_CARDS = [
  {
    id: 'new-project',
    title: 'New Project',
    description: 'Start from a requirement and build end-to-end',
    phases: ['planning', 'implementation'] as PhaseId[],
    prompt: '',
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
    prompt: '',
  },
] as const;
