"use client";

import { useQuery } from "@tanstack/react-query";
import { History, RotateCcw } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api/client";
import type { ExecutionKind, VersionSummary } from "@/lib/api/types";

const KIND_LABELS: Record<ExecutionKind, string> = {
  initial: "Inicial",
  refine: "Refino",
  rollback: "Rollback",
};

const KIND_COLORS: Record<ExecutionKind, string> = {
  initial: "bg-blue-500/15 text-blue-700 dark:text-blue-300",
  refine: "bg-amber-500/15 text-amber-700 dark:text-amber-300",
  rollback: "bg-purple-500/15 text-purple-700 dark:text-purple-300",
};

interface VersionHistoryProps {
  executionId: string;
  currentVersion: number;
  onRollback: (targetExecutionId: string) => void;
}

/**
 * Histórico de versões da linhagem (FR-41).
 *
 * Lista as versões com badge por kind, link para trocar de versão e botão
 * "Restaurar esta versão" (rollback). Some quando há só uma versão.
 */
export function VersionHistory({
  executionId,
  onRollback,
}: VersionHistoryProps) {
  const { data: versionList } = useQuery({
    queryKey: ["versions", executionId],
    queryFn: () => api.getVersions(executionId),
    staleTime: 30_000,
  });

  const [rollingBack, setRollingBack] = useState<string | null>(null);

  if (!versionList || versionList.versions.length <= 1) return null;

  const handleRollback = async (version: VersionSummary) => {
    setRollingBack(version.id);
    try {
      onRollback(version.id);
    } finally {
      setRollingBack(null);
    }
  };

  return (
    <Card>
      <CardContent className="pt-5">
        <h2 className="mb-3 flex items-center gap-2 text-sm font-medium tracking-wide text-muted-foreground uppercase">
          <History className="size-3.5" aria-hidden />
          Versões ({versionList.versions.length})
        </h2>
        <ul className="flex flex-col gap-1.5">
          {versionList.versions.map((version) => (
            <li
              key={version.id}
              className="flex items-center justify-between gap-2 rounded-md px-2 py-1.5 text-sm transition-colors hover:bg-surface-muted"
            >
              <div className="flex items-center gap-2">
                <span className="tabular-nums text-muted-foreground">
                  v{version.version}
                </span>
                <span
                  className={`rounded-full px-1.5 py-0.5 text-[10px] font-medium ${KIND_COLORS[version.kind]}`}
                >
                  {KIND_LABELS[version.kind]}
                </span>
                {version.id === executionId ? (
                  <span className="text-[10px] text-muted-foreground">
                    (atual)
                  </span>
                ) : null}
              </div>
              <div className="flex items-center gap-1">
                {version.id !== executionId ? (
                  <>
                    <Link
                      href={`/executions/${version.id}`}
                      className="text-xs text-primary underline-offset-2 hover:underline"
                    >
                      Ver
                    </Link>
                    {version.status === "succeeded" ? (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 px-1.5 text-xs"
                        disabled={rollingBack !== null}
                        onClick={() => handleRollback(version)}
                        title="Restaurar esta versão"
                      >
                        <RotateCcw className="size-3" aria-hidden />
                        {rollingBack === version.id ? "…" : ""}
                      </Button>
                    ) : null}
                  </>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
