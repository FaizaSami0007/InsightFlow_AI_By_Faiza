import { Metadata } from "next";
import { AppShell } from "@/components/shell/app-shell";
import { CollectionManagement } from "@/components/collections/collection-management";

export const metadata: Metadata = {
  title: "Dataset Collections & Federation | InsightFlow AI",
  description:
    "Manage multi-dataset collections, automated relationship discovery, referential integrity validation, and federated analytical views.",
};

export default function CollectionsPage() {
  return (
    <AppShell>
      <CollectionManagement />
    </AppShell>
  );
}
