"use client";

import { diffLines, type Change } from "diff";
import { useMemo } from "react";

interface VersionDiffProps {
  /** Markdown da versão anterior (base). */
  oldMarkdown: string;
  /** Markdown da versão atual. */
  newMarkdown: string;
}

/**
 * Diff visual entre duas versões de roteiro (FR-41).
 *
 * Usa `diffLines` do jsdiff: linhas removidas em vermelho, adicionadas em
 * verde. Coerente com a filosofia client-side do projeto (export também é).
 */
export function VersionDiff({ oldMarkdown, newMarkdown }: VersionDiffProps) {
  const changes: Change[] = useMemo(
    () => diffLines(oldMarkdown, newMarkdown),
    [oldMarkdown, newMarkdown],
  );

  return (
    <div
      className="overflow-x-auto rounded-md border border-border font-mono text-xs leading-5"
      role="region"
      aria-label="Diferenças entre versões do roteiro"
    >
      <pre className="p-4">
        {changes.map((change, index) => (
          <span
            key={index}
            className={
              change.added
                ? "block bg-green-500/15 text-green-800 dark:text-green-300"
                : change.removed
                  ? "block bg-red-500/15 text-red-800 dark:text-red-300"
                  : "block"
            }
          >
            {change.added ? "+ " : change.removed ? "- " : "  "}
            {change.value}
          </span>
        ))}
      </pre>
    </div>
  );
}
