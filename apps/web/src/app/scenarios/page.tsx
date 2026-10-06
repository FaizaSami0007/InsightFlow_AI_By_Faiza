import { Metadata } from "next";
import { AppShell } from "@/components/shell/app-shell";
import { ScenarioWorkspace } from "@/components/scenarios/scenario-workspace";

export const metadata: Metadata = {
  title: "Decision Intelligence & What-If Scenarios | InsightFlow AI",
  description:
    "Deterministic scenario simulations, parameter sensitivity sweeps, and branch comparisons with guaranteed source data immutability.",
};

export default function ScenariosPage() {
  return (
    <AppShell>
      <ScenarioWorkspace />
    </AppShell>
  );
}
