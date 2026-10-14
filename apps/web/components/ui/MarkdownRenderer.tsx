"use client";

import React, { useState } from "react";
import Icon from "./Icon";

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export default function MarkdownRenderer({ content, className = "" }: MarkdownRendererProps) {
  if (!content) return null;

  const renderedBlocks = parseMarkdownBlocks(content);

  return (
    <div className={`space-y-3 text-sm leading-relaxed text-[var(--foreground)] ${className}`}>
      {renderedBlocks}
    </div>
  );
}

function parseMarkdownBlocks(text: string): React.ReactNode[] {
  const blocks: React.ReactNode[] = [];
  const lines = text.split(/\r?\n/);
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // 1. Code blocks (```language ... ```)
    if (line.trim().startsWith("```")) {
      const match = line.trim().match(/^```([a-zA-Z0-9_-]*)/);
      const language = match ? match[1] || "text" : "text";
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      i++; // skip closing ```
      const codeContent = codeLines.join("\n");
      blocks.push(
        <CodeBlock key={`code-${i}`} language={language} code={codeContent} />
      );
      continue;
    }

    // 2. Horizontal Rule (---, ***, ___)
    if (/^(\*{3,}|-{3,}|_{3,})$/.test(line.trim())) {
      blocks.push(
        <hr
          key={`hr-${i}`}
          className="my-3 border-t border-[var(--sidebar-border)]"
        />
      );
      i++;
      continue;
    }

    // 3. Headings (# H1, ## H2, ### H3, #### H4)
    const headingMatch = line.match(/^(#{1,4})\s+(.+)$/);
    if (headingMatch) {
      const level = headingMatch[1].length;
      const headingText = headingMatch[2];
      const parsedHeading = parseInlineMarkdown(headingText);

      if (level === 1) {
        blocks.push(
          <h1 key={`h1-${i}`} className="text-lg font-bold text-[var(--foreground)] pt-2 pb-1 border-b border-[var(--sidebar-border)]">
            {parsedHeading}
          </h1>
        );
      } else if (level === 2) {
        blocks.push(
          <h2 key={`h2-${i}`} className="text-base font-semibold text-[var(--foreground)] pt-1.5 pb-0.5">
            {parsedHeading}
          </h2>
        );
      } else if (level === 3) {
        blocks.push(
          <h3 key={`h3-${i}`} className="text-sm font-semibold text-[var(--foreground)] pt-1">
            {parsedHeading}
          </h3>
        );
      } else {
        blocks.push(
          <h4 key={`h4-${i}`} className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] pt-1">
            {parsedHeading}
          </h4>
        );
      }
      i++;
      continue;
    }

    // 4. Blockquotes (> quote)
    if (line.trim().startsWith(">")) {
      const quoteLines: string[] = [];
      while (i < lines.length && lines[i].trim().startsWith(">")) {
        quoteLines.push(lines[i].trim().replace(/^>\s?/, ""));
        i++;
      }
      blocks.push(
        <blockquote
          key={`quote-${i}`}
          className="border-l-4 border-[var(--primary)] bg-[var(--sidebar-bg)]/60 px-3 py-2 rounded-r-lg text-sm italic text-[var(--foreground)]/90"
        >
          {parseInlineMarkdown(quoteLines.join(" "))}
        </blockquote>
      );
      continue;
    }

    // 5. Unordered lists (- item or * item)
    if (/^(\s*)[-*+]\s+(.+)$/.test(line)) {
      const listItems: { indent: number; text: string }[] = [];
      while (i < lines.length && /^(\s*)[-*+]\s+(.+)$/.test(lines[i])) {
        const itemMatch = lines[i].match(/^(\s*)[-*+]\s+(.+)$/);
        if (itemMatch) {
          listItems.push({
            indent: itemMatch[1].length,
            text: itemMatch[2],
          });
        }
        i++;
      }
      blocks.push(
        <ul key={`ul-${i}`} className="list-disc list-outside ml-5 space-y-1 my-1.5">
          {listItems.map((item, idx) => (
            <li key={idx} className="leading-snug" style={{ marginLeft: `${item.indent * 8}px` }}>
              {parseInlineMarkdown(item.text)}
            </li>
          ))}
        </ul>
      );
      continue;
    }

    // 6. Ordered lists (1. item)
    if (/^(\s*)\d+\.\s+(.+)$/.test(line)) {
      const listItems: { indent: number; text: string }[] = [];
      while (i < lines.length && /^(\s*)\d+\.\s+(.+)$/.test(lines[i])) {
        const itemMatch = lines[i].match(/^(\s*)\d+\.\s+(.+)$/);
        if (itemMatch) {
          listItems.push({
            indent: itemMatch[1].length,
            text: itemMatch[2],
          });
        }
        i++;
      }
      blocks.push(
        <ol key={`ol-${i}`} className="list-decimal list-outside ml-5 space-y-1 my-1.5">
          {listItems.map((item, idx) => (
            <li key={idx} className="leading-snug" style={{ marginLeft: `${item.indent * 8}px` }}>
              {parseInlineMarkdown(item.text)}
            </li>
          ))}
        </ol>
      );
      continue;
    }

    // 7. Empty lines
    if (!line.trim()) {
      i++;
      continue;
    }

    // 8. Normal paragraph
    const paraLines: string[] = [];
    while (
      i < lines.length &&
      lines[i].trim() &&
      !lines[i].trim().startsWith("```") &&
      !lines[i].match(/^(#{1,4})\s+(.+)$/) &&
      !lines[i].trim().startsWith(">") &&
      !/^(\s*)[-*+]\s+(.+)$/.test(lines[i]) &&
      !/^(\s*)\d+\.\s+(.+)$/.test(lines[i]) &&
      !/^(\*{3,}|-{3,}|_{3,})$/.test(lines[i].trim())
    ) {
      paraLines.push(lines[i]);
      i++;
    }

    blocks.push(
      <p key={`p-${i}`} className="leading-relaxed">
        {parseInlineMarkdown(paraLines.join("\n"))}
      </p>
    );
  }

  return blocks;
}

function parseInlineMarkdown(text: string): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  const regex = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[[^\]]+\]\([^)]+\)|https?:\/\/[^\s]+)/g;

  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.substring(lastIndex, match.index));
    }

    const token = match[0];

    // Bold: **text**
    if (token.startsWith("**") && token.endsWith("**")) {
      parts.push(
        <strong key={match.index} className="font-semibold text-[var(--foreground)]">
          {token.slice(2, -2)}
        </strong>
      );
    }
    // Italic: *text*
    else if (token.startsWith("*") && token.endsWith("*")) {
      parts.push(
        <em key={match.index} className="italic">
          {token.slice(1, -1)}
        </em>
      );
    }
    // Inline code: `code`
    else if (token.startsWith("`") && token.endsWith("`")) {
      parts.push(
        <code
          key={match.index}
          className="rounded bg-[var(--sidebar-border)]/60 px-1.5 py-0.5 font-mono text-[12px] text-[var(--primary)] font-medium"
        >
          {token.slice(1, -1)}
        </code>
      );
    }
    // Markdown link: [label](url)
    else if (token.startsWith("[") && token.includes("](") && token.endsWith(")")) {
      const endLabel = token.indexOf("](");
      const label = token.substring(1, endLabel);
      const url = token.substring(endLabel + 2, token.length - 1);
      parts.push(
        <a
          key={match.index}
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-[var(--primary)] underline hover:text-[var(--primary-hover)]"
        >
          {label}
        </a>
      );
    }
    // Plain URL
    else if (token.startsWith("http://") || token.startsWith("https://")) {
      parts.push(
        <a
          key={match.index}
          href={token}
          target="_blank"
          rel="noopener noreferrer"
          className="text-[var(--primary)] underline hover:text-[var(--primary-hover)]"
        >
          {token}
        </a>
      );
    }

    lastIndex = regex.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }

  return parts;
}

function CodeBlock({ language, code }: { language: string; code: string }) {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative my-2 rounded-xl border border-[var(--sidebar-border)] bg-[#1e1e2e] text-[#cdd6f4] shadow-sm overflow-hidden">
      <div className="flex items-center justify-between border-b border-white/10 px-3.5 py-1.5 text-xs text-[#a6adc8]">
        <span className="font-mono text-[11px] font-medium uppercase tracking-wider">{language}</span>
        <button
          onClick={copyToClipboard}
          className="flex items-center gap-1 rounded px-2 py-0.5 text-[11px] hover:bg-white/10 text-white/80 transition-colors"
          title="Copy code"
        >
          <Icon name={copied ? "check" : "copy"} size={12} />
          <span>{copied ? "Copied!" : "Copy"}</span>
        </button>
      </div>
      <pre className="overflow-x-auto p-3.5 font-mono text-xs leading-relaxed">
        <code>{code}</code>
      </pre>
    </div>
  );
}

