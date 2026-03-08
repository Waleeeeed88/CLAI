"use client";

import { useEffect, useState } from "react";
import { Copy, Check } from "lucide-react";
import { getHighlighter } from "../lib/highlighter";
import { cn } from "../lib/cn";

interface Props {
  code: string;
  language?: string;
}

export function CodeBlock({ code, language }: Props) {
  const [html, setHtml] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const lang = language || "plaintext";

  useEffect(() => {
    let canceled = false;
    getHighlighter()
      .then((highlighter) => {
        if (canceled) return;
        const supported = highlighter.getLoadedLanguages();
        const useLang = supported.includes(lang) ? lang : "plaintext";
        const result = highlighter.codeToHtml(code, {
          lang: useLang,
          theme: "github-dark-dimmed",
        });
        setHtml(result);
      })
      .catch(() => {});
    return () => { canceled = true; };
  }, [code, lang]);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="group relative my-2 overflow-hidden rounded-lg border border-clai-border bg-clai-surface">
      {/* Header bar */}
      <div className="flex items-center justify-between border-b border-clai-border bg-white/[0.03] px-3 py-1.5">
        <span className="text-[10px] font-mono text-clai-muted uppercase tracking-wider">
          {lang}
        </span>
        <button
          onClick={handleCopy}
          className={cn(
            "flex items-center gap-1 text-[10px] rounded px-2 py-0.5 transition-colors",
            copied
              ? "text-clai-success"
              : "text-clai-muted hover:text-clai-text",
          )}
        >
          {copied ? (
            <>
              <Check className="w-3 h-3" />
              Copied
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" />
              Copy
            </>
          )}
        </button>
      </div>

      {/* Code content */}
      {html ? (
        <div
          className="overflow-x-auto p-3 text-[13px] leading-relaxed font-mono [&_pre]:!bg-transparent [&_pre]:!m-0 [&_pre]:!p-0 [&_code]:!bg-transparent"
          dangerouslySetInnerHTML={{ __html: html }}
        />
      ) : (
        <pre className="overflow-x-auto p-3 text-[13px] leading-relaxed font-mono text-clai-text">
          <code>{code}</code>
        </pre>
      )}
    </div>
  );
}
