import { Metadata } from "next";
import { AppShell } from "@/components/shell/app-shell";
import { ObservabilityWorkspace } from "@/components/observability/observability-workspace";

export const metadata: Metadata = {
  title: "Scalability, Performance & Observability | InsightFlow AI",
  description:
    "Real-time system telemetry, latency percentiles, Prometheus metrics, multi-tenant LRU caching, and capacity load benchmarks.",
};

export default function ObservabilityPage() {
  return (
    <AppShell>
      <ObservabilityWorkspace />
    </AppShell>
  );
}
