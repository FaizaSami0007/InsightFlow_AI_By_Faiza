import { Metadata } from "next";
import { AppShell } from "@/components/shell/app-shell";
import { SecurityWorkspace } from "@/components/security/security-workspace";

export const metadata: Metadata = {
  title: "Security & Enterprise Compliance | InsightFlow AI",
  description:
    "Enterprise security posture, 15-dimension compliance scorecard, immutable audit trail, threat modeling, and adversarial AI defense.",
};

export default function SecurityPage() {
  return (
    <AppShell>
      <SecurityWorkspace />
    </AppShell>
  );
}
