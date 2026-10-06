import { Metadata } from "next";
import { AppShell } from "@/components/shell/app-shell";
import { KnowledgeCenter } from "@/components/knowledge/knowledge-center";

export const metadata: Metadata = {
  title: "Knowledge Intelligence & Business Context RAG | InsightFlow AI",
  description:
    "Grounded enterprise knowledge ingestion, semantic document chunking, hybrid vector retrieval, and deterministic evidence citations.",
};

export default function KnowledgePage() {
  return (
    <AppShell>
      <KnowledgeCenter />
    </AppShell>
  );
}
