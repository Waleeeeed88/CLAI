import { createHighlighter, type Highlighter } from 'shiki';

let highlighterPromise: Promise<Highlighter> | null = null;

export function getHighlighter(): Promise<Highlighter> {
  if (!highlighterPromise) {
    highlighterPromise = createHighlighter({
      themes: ['github-dark-dimmed'],
      langs: [
        'typescript', 'javascript', 'python', 'json', 'bash',
        'html', 'css', 'yaml', 'markdown', 'sql', 'go',
        'rust', 'java', 'tsx', 'jsx', 'shell', 'plaintext',
      ],
    });
  }
  return highlighterPromise;
}
