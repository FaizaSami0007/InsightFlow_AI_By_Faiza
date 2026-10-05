import { Metadata } from "next";
import { ForecastWorkspace } from "@/components/forecasting/forecast-workspace";

export const metadata: Metadata = {
  title: "Predictive Analytics & Forecasting | InsightFlow AI",
  description:
    "Deterministic time-series forecasting, chronological backtesting, prediction intervals, and automated model selection.",
};

export default function ForecastPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <main className="container mx-auto px-4 py-8 max-w-7xl">
        <ForecastWorkspace />
      </main>
    </div>
  );
}
