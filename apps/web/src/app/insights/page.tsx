import { Metadata } from "next";
import { AppShell } from "@/components/shell/app-shell";
import { AnomalyWorkspace } from "@/components/anomalies/anomaly-workspace";

export const metadata: Metadata = {
  title: "Anomaly Detection & Proactive Insights | InsightFlow AI",
  description:
    "Deterministic statistical anomaly detection, dimensional root-cause contribution breakdown, and explainable proactive analytical insights.",
};

export default function InsightsPage() {
  return (
    <AppShell>
      <AnomalyWorkspace />
    </AppShell>
  );
}
