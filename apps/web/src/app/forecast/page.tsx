import { Metadata } from "next";
import { AppShell } from "@/components/shell/app-shell";
import { ForecastWorkspace } from "@/components/forecasting/forecast-workspace";

export const metadata: Metadata = {
  title: "Predictive Analytics & Forecasting | InsightFlow AI",
  description:
    "Deterministic time-series forecasting, chronological backtesting, prediction intervals, and automated model selection.",
};

export default function ForecastPage() {
  return (
    <AppShell>
      <ForecastWorkspace />
    </AppShell>
  );
}
