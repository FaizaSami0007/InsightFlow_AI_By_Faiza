import { Metadata } from "next";
import { AnomalyWorkspace } from "@/components/anomalies/anomaly-workspace";

export const metadata: Metadata = {
  title: "Anomaly Detection & Proactive Insights | InsightFlow AI",
  description:
    "Deterministic statistical anomaly detection, dimensional root-cause contribution breakdown, and explainable proactive analytical insights.",
};

export default function InsightsPage() {
  return (
    <div className="container mx-auto max-w-7xl px-4 py-8 md:px-6">
      <AnomalyWorkspace />
    </div>
  );
}
