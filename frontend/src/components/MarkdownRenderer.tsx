"use client";

import ReactMarkdown from "react-markdown";
import { CodeBlock } from "./CodeBlock";

interface Props {
  content: string;
}

export function MarkdownRenderer({ content }: Props) {
  return (
    <ReactMarkdown
      className="prose prose-sm prose-clai max-w-none"
      components={{
        code({ className, children, ...props }) {
          const match = /language-(\w+)/.exec(className || "");
          const codeString = String(children).replace(/\n$/, "");

          // Block code (has language class or is inside pre)
          if (match || (codeString.includes("\n") && !className)) {
            return <CodeBlock code={codeString} language={match?.[1]} />;
          }

          // Inline code
          return (
            <code
              className="rounded bg-clai-card px-1.5 py-0.5 text-[0.85em] font-mono text-clai-text"
              {...props}
            >
              {children}
            </code>
          );
        },
        pre({ children }) {
          // If the child is already a CodeBlock, just return it
          return <>{children}</>;
        },
        a({ href, children }) {
          return (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-clai-text underline decoration-white/20 underline-offset-4 hover:decoration-white/60"
            >
              {children}
            </a>
          );
        },
        table({ children }) {
          return (
            <div className="overflow-x-auto my-2">
              <table className="min-w-full text-xs border-collapse border border-clai-border rounded">
                {children}
              </table>
            </div>
          );
        },
        th({ children }) {
          return (
            <th className="border border-clai-border bg-clai-surface px-3 py-1.5 text-left text-clai-text font-medium">
              {children}
            </th>
          );
        },
        td({ children }) {
          return (
            <td className="border border-clai-border px-3 py-1.5 text-clai-muted">
              {children}
            </td>
          );
        },
      }}
    >
      {content}
    </ReactMarkdown>
  );
}
