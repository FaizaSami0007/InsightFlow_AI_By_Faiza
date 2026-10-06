import { Metadata } from "next";
import { ScenarioWorkspace } from "@/components/scenarios/scenario-workspace";

export const metadata: Metadata = {
  title: "Decision Intelligence & What-If Scenarios | InsightFlow AI",
  description:
    "Deterministic scenario simulations, parameter sensitivity sweeps, and branch comparisons with guaranteed source data immutability.",
};

export default function ScenariosPage() {
  return (
    <div className="container mx-auto max-w-7xl px-4 py-8 md:px-6">
      <ScenarioWorkspace />
    </div>
  );
}
