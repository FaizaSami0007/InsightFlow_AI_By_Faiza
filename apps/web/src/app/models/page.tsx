import { Metadata } from "next";
import { ModelOperationsView } from "@/components/models/model-operations-view";

export const metadata: Metadata = {
  title: "Production MLOps & Model Operations | InsightFlow AI",
  description:
    "Enterprise model registry, immutable versioning, PSI drift monitoring, and multi-factor model health indicators.",
};

export default function ModelsPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <main className="container mx-auto px-4 py-8 max-w-7xl">
        <ModelOperationsView />
      </main>
    </div>
  );
}
