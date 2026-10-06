import { Metadata } from "next";
import { KnowledgeCenter } from "@/components/knowledge/knowledge-center";

export const metadata: Metadata = {
  title: "Knowledge Intelligence & Business Context RAG | InsightFlow AI",
  description:
    "Grounded enterprise knowledge ingestion, semantic document chunking, hybrid vector retrieval, and deterministic evidence citations.",
};

export default function KnowledgePage() {
  return (
    <div className="min-h-screen bg-background text-ink">
      <main className="container mx-auto px-4 py-8 max-w-7xl">
        <KnowledgeCenter />
      </main>
    </div>
  );
}
