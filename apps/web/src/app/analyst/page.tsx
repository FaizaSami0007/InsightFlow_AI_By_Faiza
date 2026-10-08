"use client";

import React, { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { AppShell } from "@/components/shell/app-shell";
import { AIAnalystView } from "@/components/analyst/ai-analyst-view";
import { LoadingState } from "@/components/states/loading-state";

function AnalystPageContent() {
  const searchParams = useSearchParams();
  const datasetId = searchParams.get("dataset_id") || undefined;
  const versionId = searchParams.get("version_id") || undefined;

  return (
    <div className="w-full">
      <AIAnalystView initialDatasetId={datasetId} initialVersionId={versionId} />
    </div>
  );
}

export default function AnalystPage() {
  return (
    <AppShell>
      <Suspense
        fallback={
          <div className="flex h-96 items-center justify-center">
            <LoadingState title="Loading AI Analyst" description="Initializing orchestrator environment..." />
          </div>
        }
      >
        <AnalystPageContent />
      </Suspense>
    </AppShell>
  );
}
