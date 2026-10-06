import { Metadata } from "next";
import { SecurityWorkspace } from "@/components/security/security-workspace";

export const metadata: Metadata = {
  title: "Security & Enterprise Compliance | InsightFlow AI",
  description:
    "Enterprise security posture, 15-dimension compliance scorecard, immutable audit trail, threat modeling, and adversarial AI defense.",
};

export default function SecurityPage() {
  return (
    <div className="container mx-auto max-w-7xl px-4 py-8 md:px-6">
      <SecurityWorkspace />
    </div>
  );
}
