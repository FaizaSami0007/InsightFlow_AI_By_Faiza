import { Metadata } from "next";
import { ObservabilityWorkspace } from "@/components/observability/observability-workspace";

export const metadata: Metadata = {
  title: "Scalability, Performance & Observability | InsightFlow AI",
  description:
    "Real-time system telemetry, latency percentiles, Prometheus metrics, multi-tenant LRU caching, and capacity load benchmarks.",
};

export default function ObservabilityPage() {
  return (
    <div className="container mx-auto max-w-7xl px-4 py-8 md:px-6">
      <ObservabilityWorkspace />
    </div>
  );
}
