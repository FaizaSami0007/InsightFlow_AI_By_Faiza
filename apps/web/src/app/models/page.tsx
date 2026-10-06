import { Metadata } from "next";
import { AppShell } from "@/components/shell/app-shell";
import { ModelOperationsView } from "@/components/models/model-operations-view";

export const metadata: Metadata = {
  title: "Production MLOps & Model Operations | InsightFlow AI",
  description:
    "Enterprise model registry, immutable versioning, PSI drift monitoring, and multi-factor model health indicators.",
};

export default function ModelsPage() {
  return (
    <AppShell>
      <ModelOperationsView />
    </AppShell>
  );
}
