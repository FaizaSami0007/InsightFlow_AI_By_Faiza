import { Metadata } from "next";
import { ScenarioWorkspace } from "@/components/scenarios/scenario-workspace";

export const metadata: Metadata = {
  title: "Decision Intelligence & What-If Scenarios | InsightFlow AI",
  description:
    "Deterministic scenario simulations, parameter sensitivity sweeps, and branch comparisons with guaranteed source data immutability.",
};

export default function ScenariosPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <main className="container mx-auto px-4 py-8 max-w-7xl">
        <ScenarioWorkspace />
      </main>
    </div>
  );
}
