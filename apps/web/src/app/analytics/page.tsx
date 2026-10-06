import { Metadata } from "next";
import { AppShell } from "@/components/shell/app-shell";
import { AnalyticsWorkspace } from "@/components/analytics/analytics-workspace";

export const metadata: Metadata = {
  title: "Deterministic Analytics Engine | InsightFlow AI",
  description:
    "Execute SQL aggregations, descriptive statistics, Pearson correlations, time-series trends, and Tukey IQR outlier models with DuckDB.",
};

export default function AnalyticsPage() {
  return (
    <AppShell>
      <AnalyticsWorkspace />
    </AppShell>
  );
}
