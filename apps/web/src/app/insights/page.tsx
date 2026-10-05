import { Metadata } from "next";
import { AnomalyWorkspace } from "@/components/anomalies/anomaly-workspace";

export const metadata: Metadata = {
  title: "Anomaly Detection & Proactive Insights | InsightFlow AI",
  description:
    "Deterministic statistical anomaly detection, dimensional root-cause contribution breakdown, and explainable proactive analytical insights.",
};

export default function InsightsPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <main className="container mx-auto px-4 py-8 max-w-7xl">
        <AnomalyWorkspace />
      </main>
    </div>
  );
}
