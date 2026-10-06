import { Metadata } from "next";
import { ForecastWorkspace } from "@/components/forecasting/forecast-workspace";

export const metadata: Metadata = {
  title: "Predictive Analytics & Forecasting | InsightFlow AI",
  description:
    "Deterministic time-series forecasting, chronological backtesting, prediction intervals, and automated model selection.",
};

export default function ForecastPage() {
  return (
    <div className="container mx-auto max-w-7xl px-4 py-8 md:px-6">
      <ForecastWorkspace />
    </div>
  );
}
