import { Metadata } from "next";
import { ModelOperationsView } from "@/components/models/model-operations-view";

export const metadata: Metadata = {
  title: "Production MLOps & Model Operations | InsightFlow AI",
  description:
    "Enterprise model registry, immutable versioning, PSI drift monitoring, and multi-factor model health indicators.",
};

export default function ModelsPage() {
  return (
    <div className="container mx-auto max-w-7xl px-4 py-8 md:px-6">
      <ModelOperationsView />
    </div>
  );
}
