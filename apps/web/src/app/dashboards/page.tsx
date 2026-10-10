"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  LayoutDashboard,
  Plus,
  Layers,
  Sparkles,
  ArrowRight,
  Search,
  Trash2,
} from "lucide-react";
import { AppShell } from "@/components/shell/app-shell";
import { DashboardGeneratorModal } from "@/components/dashboards/dashboard-generator-modal";
import { Dashboard, Dataset } from "@/types";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api-client";

const DEMO_FALLBACK_DATASET: Dataset = {
  id: "a309c861-5e76-4dda-a84a-5651aa925317",
  name: "Insightflow Sales Transactions Sample",
  description: "Retail transactions demo dataset with pricing, volume, and customer segmentation.",
  status: "READY",
  created_at: "2026-10-06T17:42:33.866564Z",
  updated_at: "2026-10-06T17:42:33.866564Z",
  version_count: 1,
  latest_version: {
    id: "f2bb5357-97ea-4b2c-86f4-ea5c2c2eea51",
    dataset_id: "a309c861-5e76-4dda-a84a-5651aa925317",
    version_number: 1,
    file_name: "insightflow_sales_transactions_sample.csv",
    file_format: "CSV",
    file_size: 55206,
    checksum: "0f4c74b431d7c8b51929e5f876093244b787f9ed709869ce526b882aaa62f6e5",
    status: "READY",
    row_count: 500,
    column_count: 17,
    created_at: "2026-10-06T17:42:33.866564Z",
  },
};

export default function DashboardsListPage() {
  const router = useRouter();
  const [dashboards, setDashboards] = React.useState<Dashboard[]>([]);
  const [datasets, setDatasets] = React.useState<Dataset[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);
  const [searchQuery, setSearchQuery] = React.useState("");
  const [isGeneratorOpen, setIsGeneratorOpen] = React.useState(false);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [dashboardsData, datasetsData] = await Promise.allSettled([
        api.get<Dashboard[] | { items: Dashboard[] }>("/api/v1/dashboards"),
        api.get<Dataset[] | { items: Dataset[] }>("/api/v1/datasets"),
      ]);

      if (dashboardsData.status === "fulfilled") {
        const val = dashboardsData.value;
        setDashboards(Array.isArray(val) ? val : (val as { items: Dashboard[] }).items || []);
      }
      if (datasetsData.status === "fulfilled") {
        const val = datasetsData.value;
        const list = Array.isArray(val) ? val : (val as { items: Dataset[] }).items || [];
        setDatasets(list.length > 0 ? list : [DEMO_FALLBACK_DATASET]);
      } else {
        setDatasets([DEMO_FALLBACK_DATASET]);
      }
    } catch {
      setDatasets([DEMO_FALLBACK_DATASET]);
    } finally {
      setIsLoading(false);
    }
  };

  React.useEffect(() => {
    fetchData();
  }, []);

  const handleDeleteDashboard = async (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this dashboard?")) return;

    try {
      await api.delete(`/api/v1/dashboards/${id}`);
      setDashboards((prev) => prev.filter((d) => d.id !== id));
    } catch {
      // Ignore
    }
  };

  const filteredDashboards = dashboards.filter((d) =>
    (d.name && d.name.toLowerCase().includes(searchQuery.toLowerCase())) ||
    (d.description && d.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <AppShell>
      <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-6">
        {/* Header with Title & Create CTA */}
        <header className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="flex items-center gap-2 text-teal font-semibold text-xs tracking-wider uppercase">
              <Sparkles className="h-3.5 w-3.5" />
              <span>Phase 8 Context-Aware Dashboard Intelligence</span>
            </div>
            <h1 className="text-lg sm:text-xl lg:text-2xl font-bold tracking-tight text-ink mt-1">
              Analytics Dashboards
            </h1>
            <p className="text-xs text-slate mt-1">
              AI-generated, grounded, deterministic analytical dashboards with structured provenance.
            </p>
          </div>

          <button
            onClick={() => setIsGeneratorOpen(true)}
            className="inline-flex items-center gap-2 rounded-xl bg-teal px-4 py-2.5 text-xs font-semibold text-white shadow-soft hover:bg-teal-hover transition-colors focus-visible:ring-2 focus-visible:ring-teal"
          >
            <Plus className="h-4 w-4" />
            <span>Generate Dashboard</span>
          </button>
        </header>

        {/* Search & Filter bar */}
        <div className="flex items-center justify-between gap-4">
          <div className="relative w-full max-w-md">
            <Search className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search dashboards by title or purpose..."
              className="w-full rounded-xl border border-border bg-surface py-2 pl-10 pr-4 text-xs text-ink placeholder:text-slate/60 focus:border-teal focus:outline-none focus:ring-2 focus:ring-teal/20"
            />
          </div>
          <div className="text-xs text-slate">
            Total: <strong className="text-ink">{dashboards.length}</strong> dashboards
          </div>
        </div>

        {/* Dashboards Gallery Grid */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-48 rounded-2xl border border-border bg-surface animate-pulse p-6" />
            ))}
          </div>
        ) : filteredDashboards.length === 0 ? (
          <div className="rounded-2xl border-2 border-dashed border-border bg-surface/50 p-12 text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-teal-soft text-teal">
              <LayoutDashboard className="h-6 w-6" />
            </div>
            <h3 className="mt-4 text-sm font-semibold text-ink">No dashboards found</h3>
            <p className="mt-1 text-xs text-slate max-w-sm mx-auto">
              {searchQuery
                ? "No dashboards match your search query."
                : "Create your first AI-driven dashboard by selecting a dataset and providing analytical intent."}
            </p>
            {!searchQuery && (
              <button
                onClick={() => setIsGeneratorOpen(true)}
                className="mt-4 inline-flex items-center gap-2 rounded-xl bg-teal px-4 py-2 text-xs font-semibold text-white shadow-soft hover:bg-teal-hover transition-colors"
              >
                <Plus className="h-4 w-4" />
                <span>Create Dashboard</span>
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {filteredDashboards.map((dash) => (
              <Link
                key={dash.id}
                href={`/dashboards/${dash.id}`}
                className="group flex flex-col justify-between rounded-2xl border border-border bg-surface p-5 shadow-soft hover:border-teal/50 hover:shadow-soft-lg transition-all focus-visible:ring-2 focus-visible:ring-teal"
              >
                <div className="space-y-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-teal-soft text-teal group-hover:bg-teal group-hover:text-white transition-colors">
                        <LayoutDashboard className="h-4 w-4" />
                      </div>
                      <span
                        className={cn(
                          "rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider",
                          dash.status === "READY" && "bg-teal-soft text-teal",
                          dash.status === "GENERATING" && "bg-amber-50 text-amber-700",
                          dash.status === "PARTIAL" && "bg-amber-100 text-amber-800",
                          dash.status === "FAILED" && "bg-rose/10 text-rose"
                        )}
                      >
                        {dash.status}
                      </span>
                    </div>

                    <button
                      onClick={(e) => handleDeleteDashboard(dash.id, e)}
                      className="rounded-lg p-1.5 text-slate/60 hover:bg-rose/10 hover:text-rose transition-colors"
                      title="Delete dashboard"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>

                  <div>
                    <h3 className="text-sm font-semibold text-ink group-hover:text-teal transition-colors">
                      {dash.name}
                    </h3>
                    {dash.description && (
                      <p className="mt-1 text-xs text-slate line-clamp-2 leading-relaxed">
                        {dash.description}
                      </p>
                    )}
                  </div>
                </div>

                <div className="mt-4 border-t border-border pt-3 flex items-center justify-between text-[11px] text-slate">
                  <div className="flex items-center gap-3">
                    <span className="flex items-center gap-1">
                      <Layers className="h-3 w-3 text-teal" />
                      {dash.dataset_id}
                    </span>
                    <span>{dash.widgets.length} widgets</span>
                  </div>
                  <div className="flex items-center gap-1 text-teal font-medium group-hover:translate-x-0.5 transition-transform">
                    <span>Open</span>
                    <ArrowRight className="h-3 w-3" />
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}

        {/* Dashboard Generator Modal */}
        <DashboardGeneratorModal
          isOpen={isGeneratorOpen}
          onClose={() => setIsGeneratorOpen(false)}
          datasets={datasets}
          onDashboardCreated={(newDashboard) => {
            setIsGeneratorOpen(false);
            router.push(`/dashboards/${newDashboard.id}`);
          }}
        />
      </div>
    </AppShell>
  );
}
