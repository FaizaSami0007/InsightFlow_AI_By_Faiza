import { Metadata } from "next";
import { CollectionManagement } from "@/components/collections/collection-management";

export const metadata: Metadata = {
  title: "Dataset Collections & Federation | InsightFlow AI",
  description:
    "Manage multi-dataset collections, automated relationship discovery, referential integrity validation, and federated analytical views.",
};

export default function CollectionsPage() {
  return (
    <div className="min-h-screen bg-background">
      <main className="container mx-auto px-4 py-8 max-w-7xl">
        <CollectionManagement />
      </main>
    </div>
  );
}
