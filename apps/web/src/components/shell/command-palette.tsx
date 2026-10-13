"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import {
  Activity,
  ArrowRight,
  BookOpen,
  Bot,
  Cpu,
  Database,
  Layers,
  LayoutDashboard,
  LineChart,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  TrendingUp,
  X,
  Zap,
  Plus,
  Compass,
} from "lucide-react";
import { useShellStore } from "@/stores/use-shell-store";
import { api } from "@/lib/api-client";
import { Dataset, Dashboard } from "@/types";
import { cn } from "@/lib/utils";

interface SearchResultItem {
  id: string;
  category: "Navigation" | "Datasets" | "Dashboards" | "Actions";
  title: string;
  subtitle?: string;
  icon: React.ComponentType<{ className?: string }>;
  href: string;
  badge?: string;
  badgeColor?: "teal" | "blue" | "amber" | "slate";
}

const MODULE_ITEMS: SearchResultItem[] = [
  {
    id: "nav-overview",
    category: "Navigation",
    title: "Platform Overview",
    subtitle: "High-level summary, executive metrics, and recent workspace activity",
    icon: Layers,
    href: "/",
    badge: "Dashboard",
    badgeColor: "teal",
  },
  {
    id: "nav-datasets",
    category: "Navigation",
    title: "Datasets & Lineage",
    subtitle: "Upload, inspect schemas, semantic profiles, and data versions",
    icon: Database,
    href: "/datasets",
    badge: "Core",
    badgeColor: "blue",
  },
  {
    id: "nav-collections",
    category: "Navigation",
    title: "Collections & Federation",
    subtitle: "Federate multi-source data collections and enterprise cataloging",
    icon: Layers,
    href: "/collections",
    badge: "Data",
    badgeColor: "slate",
  },
  {
    id: "nav-connections",
    category: "Navigation",
    title: "Data Connections",
    subtitle: "Manage external database connectors, warehouses, and storage sources",
    icon: Zap,
    href: "/connections",
    badge: "Integration",
    badgeColor: "amber",
  },
  {
    id: "nav-analytics",
    category: "Navigation",
    title: "Analytics Engine",
    subtitle: "Deterministic computations, statistical profiles, and DuckDB queries",
    icon: LineChart,
    href: "/analytics",
    badge: "Compute",
    badgeColor: "teal",
  },
  {
    id: "nav-analyst",
    category: "Navigation",
    title: "AI Analyst Studio",
    subtitle: "Grounded natural-language conversational analytical agent",
    icon: Bot,
    href: "/analyst",
    badge: "AI Agent",
    badgeColor: "teal",
  },
  {
    id: "nav-dashboards",
    category: "Navigation",
    title: "Dashboards",
    subtitle: "Context-aware automated and custom analytical dashboards",
    icon: LayoutDashboard,
    href: "/dashboards",
    badge: "BI",
    badgeColor: "blue",
  },
  {
    id: "nav-forecast",
    category: "Navigation",
    title: "Forecasting & Trends",
    subtitle: "Predictive ML forecasting, seasonal projections, and confidence intervals",
    icon: TrendingUp,
    href: "/forecast",
    badge: "ML",
    badgeColor: "blue",
  },
  {
    id: "nav-insights",
    category: "Navigation",
    title: "Insights & Anomalies",
    subtitle: "Automated statistical anomaly detection and metric driver analysis",
    icon: Zap,
    href: "/insights",
    badge: "Signals",
    badgeColor: "amber",
  },
  {
    id: "nav-scenarios",
    category: "Navigation",
    title: "Scenarios & What-If",
    subtitle: "Counterfactual scenario simulations and parameter sensitivity",
    icon: SlidersHorizontal,
    href: "/scenarios",
    badge: "Simulation",
    badgeColor: "slate",
  },
  {
    id: "nav-models",
    category: "Navigation",
    title: "Model Operations",
    subtitle: "MLOps registry, drift tracking, and end-to-end provenance DAGs",
    icon: Cpu,
    href: "/models",
    badge: "MLOps",
    badgeColor: "slate",
  },
  {
    id: "nav-knowledge",
    category: "Navigation",
    title: "Knowledge Center",
    subtitle: "Domain ontologies, business glossary, and RAG semantic citations",
    icon: BookOpen,
    href: "/knowledge",
    badge: "Catalog",
    badgeColor: "slate",
  },
  {
    id: "nav-security",
    category: "Navigation",
    title: "Security & Compliance",
    subtitle: "RBAC policies, column allowlists, and immutable audit logs",
    icon: ShieldCheck,
    href: "/security",
    badge: "Governance",
    badgeColor: "teal",
  },
  {
    id: "nav-observability",
    category: "Navigation",
    title: "Observability & Scaling",
    subtitle: "API latencies, token consumption, worker status, and audit telemetry",
    icon: Activity,
    href: "/observability",
    badge: "System",
    badgeColor: "slate",
  },
];

const DEFAULT_ACTIONS: SearchResultItem[] = [
  {
    id: "action-new-dashboard",
    category: "Actions",
    title: "Generate New Dashboard",
    subtitle: "Launch AI-driven or template-based dashboard creation",
    icon: Plus,
    href: "/dashboards",
    badge: "Action",
    badgeColor: "teal",
  },
  {
    id: "action-ask-ai",
    category: "Actions",
    title: "Ask AI Analyst a Question",
    subtitle: "Start a grounded analytical inquiry with interactive visualizations",
    icon: Bot,
    href: "/analyst",
    badge: "Action",
    badgeColor: "teal",
  },
  {
    id: "action-upload-dataset",
    category: "Actions",
    title: "Upload & Register Dataset",
    subtitle: "Import a CSV or Parquet file into the deterministic storage layer",
    icon: Database,
    href: "/datasets",
    badge: "Action",
    badgeColor: "blue",
  },
  {
    id: "action-run-forecast",
    category: "Actions",
    title: "Run Time-Series Forecast",
    subtitle: "Forecast temporal revenue, transactions, or volume metrics",
    icon: TrendingUp,
    href: "/forecast",
    badge: "Action",
    badgeColor: "blue",
  },
];

export function CommandPalette() {
  const router = useRouter();
  const { isSearchOpen, setIsSearchOpen } = useShellStore();
  const [query, setQuery] = React.useState("");
  const [datasets, setDatasets] = React.useState<Dataset[]>([]);
  const [dashboards, setDashboards] = React.useState<Dashboard[]>([]);
  const [isLoadingData, setIsLoadingData] = React.useState(false);
  const [selectedIndex, setSelectedIndex] = React.useState(0);
  const inputRef = React.useRef<HTMLInputElement>(null);
  const listRef = React.useRef<HTMLDivElement>(null);

  // Global Ctrl+K / Cmd+K keybinding listener
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setIsSearchOpen(!isSearchOpen);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isSearchOpen, setIsSearchOpen]);

  // Focus input and fetch data when opened
  React.useEffect(() => {
    if (isSearchOpen) {
      setQuery("");
      setSelectedIndex(0);
      const timer = setTimeout(() => {
        inputRef.current?.focus();
      }, 50);

      // Fetch dynamic datasets and dashboards if not already loaded
      async function loadEntities() {
        setIsLoadingData(true);
        try {
          const [dsRes, dashRes] = await Promise.allSettled([
            api.get<{ items: Dataset[] } | Dataset[]>("/api/v1/datasets"),
            api.get<{ items: Dashboard[] } | Dashboard[]>("/api/v1/dashboards"),
          ]);
          if (dsRes.status === "fulfilled") {
            const val = dsRes.value;
            setDatasets(Array.isArray(val) ? val : val?.items || []);
          }
          if (dashRes.status === "fulfilled") {
            const val = dashRes.value;
            setDashboards(Array.isArray(val) ? val : val?.items || []);
          }
        } catch {
          // Gracefully fallback to static modules
        } finally {
          setIsLoadingData(false);
        }
      }
      loadEntities();

      return () => clearTimeout(timer);
    }
  }, [isSearchOpen]);

  // Compute filtered results
  const filteredResults = React.useMemo<SearchResultItem[]>(() => {
    const q = query.trim().toLowerCase();

    // 1. Dynamic Dataset items
    const datasetItems: SearchResultItem[] = datasets.map((d) => ({
      id: `ds-${d.id}`,
      category: "Datasets",
      title: d.name,
      subtitle: d.description || `Dataset ID: ${d.id.slice(0, 8)}... • Status: ${d.status}`,
      icon: Database,
      href: "/datasets",
      badge: d.latest_version?.row_count
        ? `${d.latest_version.row_count.toLocaleString()} rows`
        : d.status,
      badgeColor: "blue",
    }));

    // 2. Dynamic Dashboard items
    const dashboardItems: SearchResultItem[] = dashboards.map((d) => ({
      id: `dash-${d.id}`,
      category: "Dashboards",
      title: d.name,
      subtitle: d.description || `Dashboard ID: ${d.id.slice(0, 8)}... • ${d.widgets?.length || 0} widgets`,
      icon: LayoutDashboard,
      href: `/dashboards/${d.id}`,
      badge: `${d.widgets?.length || 0} widgets`,
      badgeColor: "teal",
    }));

    if (!q) {
      // Empty query shows Quick Actions, top modules, and first few datasets/dashboards
      return [
        ...DEFAULT_ACTIONS,
        ...MODULE_ITEMS.slice(0, 5),
        ...datasetItems.slice(0, 3),
        ...dashboardItems.slice(0, 3),
      ];
    }

    // AI custom query prompt item at the top when searching
    const aiActionItem: SearchResultItem = {
      id: "ai-prompt-query",
      category: "Actions",
      title: `Ask AI Analyst: "${query.trim()}"`,
      subtitle: "Execute natural language analysis and visualize findings",
      icon: Sparkles,
      href: `/analyst?q=${encodeURIComponent(query.trim())}`,
      badge: "AI Query",
      badgeColor: "teal",
    };

    const matchedDatasets = datasetItems.filter(
      (item) =>
        item.title.toLowerCase().includes(q) ||
        (item.subtitle && item.subtitle.toLowerCase().includes(q))
    );

    const matchedDashboards = dashboardItems.filter(
      (item) =>
        item.title.toLowerCase().includes(q) ||
        (item.subtitle && item.subtitle.toLowerCase().includes(q))
    );

    const matchedModules = MODULE_ITEMS.filter(
      (item) =>
        item.title.toLowerCase().includes(q) ||
        (item.subtitle && item.subtitle.toLowerCase().includes(q))
    );

    const matchedActions = DEFAULT_ACTIONS.filter(
      (item) =>
        item.title.toLowerCase().includes(q) ||
        (item.subtitle && item.subtitle.toLowerCase().includes(q))
    );

    return [
      aiActionItem,
      ...matchedDatasets,
      ...matchedDashboards,
      ...matchedModules,
      ...matchedActions,
    ];
  }, [query, datasets, dashboards]);

  // Keep selected index within bounds
  React.useEffect(() => {
    if (selectedIndex >= filteredResults.length) {
      setSelectedIndex(Math.max(0, filteredResults.length - 1));
    }
  }, [filteredResults.length, selectedIndex]);

  const handleSelect = (item: SearchResultItem) => {
    setIsSearchOpen(false);
    router.push(item.href);
  };

  // Keyboard navigation inside modal
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % Math.max(1, filteredResults.length));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + filteredResults.length) % Math.max(1, filteredResults.length));
    } else if (e.key === "Enter") {
      e.preventDefault();
      const current = filteredResults[selectedIndex];
      if (current) {
        handleSelect(current);
      }
    } else if (e.key === "Escape") {
      e.preventDefault();
      setIsSearchOpen(false);
    }
  };

  if (!isSearchOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center p-3 sm:p-6 pt-[8vh] sm:pt-[12vh]"
      role="dialog"
      aria-modal="true"
      aria-label="Global Search and Command Palette"
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-ink/50 backdrop-blur-sm transition-opacity animate-in fade-in duration-150"
        onClick={() => setIsSearchOpen(false)}
        aria-hidden="true"
      />

      {/* Command Palette Card */}
      <div className="relative z-50 w-full max-w-2xl overflow-hidden rounded-2xl border border-border bg-surface shadow-soft-xl transition-all animate-in fade-in zoom-in-95 duration-150 flex flex-col max-h-[75vh]">
        {/* Search Input Bar */}
        <div className="flex items-center gap-3 border-b border-border px-4 py-3 bg-cloud/20">
          <Search className="h-5 w-5 text-teal shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            onKeyDown={handleKeyDown}
            placeholder="Search datasets, dashboards, modules, or ask AI..."
            className="flex-1 bg-transparent text-sm text-ink placeholder:text-slate focus:outline-none min-w-0"
            aria-label="Search across platform"
          />
          {query ? (
            <button
              onClick={() => {
                setQuery("");
                setSelectedIndex(0);
                inputRef.current?.focus();
              }}
              className="p-1 rounded-lg text-slate hover:text-ink hover:bg-cloud"
              aria-label="Clear search"
            >
              <X className="h-4 w-4" />
            </button>
          ) : (
            <kbd className="hidden sm:inline-flex items-center rounded-lg border border-border bg-cloud px-2 py-0.5 text-[10px] font-semibold text-slate uppercase">
              ESC to close
            </kbd>
          )}
        </div>

        {/* Results List */}
        <div
          ref={listRef}
          className="flex-1 overflow-y-auto overscroll-contain p-2 space-y-1 divide-y divide-border/20"
        >
          {filteredResults.length === 0 ? (
            <div className="p-8 text-center space-y-2">
              <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-xl bg-cloud text-slate">
                <Compass className="h-5 w-5" />
              </div>
              <p className="text-sm font-semibold text-ink">No results found</p>
              <p className="text-xs text-slate">
                No matching datasets, dashboards, or modules for &quot;{query}&quot;.
              </p>
              <button
                onClick={() => {
                  setIsSearchOpen(false);
                  router.push(`/analyst?q=${encodeURIComponent(query)}`);
                }}
                className="inline-flex items-center gap-1.5 rounded-xl bg-teal px-3.5 py-1.5 text-xs font-semibold text-white shadow-soft hover:bg-teal-hover transition-colors mt-2"
              >
                <Sparkles className="h-3.5 w-3.5" />
                <span>Ask AI Analyst about this</span>
              </button>
            </div>
          ) : (
            filteredResults.map((item, idx) => {
              const Icon = item.icon;
              const isSelected = idx === selectedIndex;

              return (
                <div
                  key={item.id}
                  onClick={() => handleSelect(item)}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={cn(
                    "group flex items-center justify-between gap-3 px-3.5 py-2.5 rounded-xl cursor-pointer transition-all select-none",
                    isSelected
                      ? "bg-teal-soft text-ink border border-teal-border shadow-xs"
                      : "hover:bg-cloud text-slate hover:text-ink border border-transparent"
                  )}
                  role="option"
                  aria-selected={isSelected}
                >
                  <div className="flex items-center gap-3 min-w-0 flex-1">
                    <div
                      className={cn(
                        "flex h-8 w-8 shrink-0 items-center justify-center rounded-xl transition-colors",
                        isSelected
                          ? "bg-teal text-white shadow-soft"
                          : "bg-cloud text-slate group-hover:bg-surface group-hover:text-ink border border-border/60"
                      )}
                    >
                      <Icon className="h-4 w-4" />
                    </div>

                    <div className="flex flex-col min-w-0 leading-tight">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span
                          className={cn(
                            "text-xs font-semibold truncate",
                            isSelected ? "text-ink" : "text-ink"
                          )}
                        >
                          {item.title}
                        </span>
                        {item.badge && (
                          <span
                            className={cn(
                              "text-[10px] font-semibold px-2 py-0.2 rounded-full uppercase tracking-wider shrink-0 border",
                              item.badgeColor === "teal" &&
                                "bg-teal/10 text-teal border-teal/20",
                              item.badgeColor === "blue" &&
                                "bg-blue/10 text-blue border-blue/20",
                              item.badgeColor === "amber" &&
                                "bg-amber/10 text-amber border-amber/20",
                              (!item.badgeColor || item.badgeColor === "slate") &&
                                "bg-cloud text-slate border-border"
                            )}
                          >
                            {item.badge}
                          </span>
                        )}
                      </div>
                      {item.subtitle && (
                        <p className="text-[11px] text-slate truncate mt-0.5">
                          {item.subtitle}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-[10px] text-slate/60 font-medium hidden sm:inline">
                      {item.category}
                    </span>
                    <ArrowRight
                      className={cn(
                        "h-3.5 w-3.5 transition-transform",
                        isSelected
                          ? "text-teal translate-x-0.5"
                          : "text-slate/40 group-hover:text-slate"
                      )}
                    />
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer / Helper Shortcuts */}
        <div className="flex items-center justify-between border-t border-border bg-cloud/40 px-4 py-2 text-[11px] text-slate shrink-0">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1">
              <kbd className="rounded border border-border bg-surface px-1.5 py-0.5 text-[9px] font-mono">
                ↑
              </kbd>
              <kbd className="rounded border border-border bg-surface px-1.5 py-0.5 text-[9px] font-mono">
                ↓
              </kbd>{" "}
              Navigate
            </span>
            <span className="flex items-center gap-1">
              <kbd className="rounded border border-border bg-surface px-1.5 py-0.5 text-[9px] font-mono">
                ↵
              </kbd>{" "}
              Select
            </span>
            <span className="flex items-center gap-1">
              <kbd className="rounded border border-border bg-surface px-1.5 py-0.5 text-[9px] font-mono">
                ESC
              </kbd>{" "}
              Close
            </span>
          </div>

          <div className="flex items-center gap-1 text-[10px] text-teal font-medium">
            <Sparkles className="h-3 w-3" />
            <span>InsightFlow Command Center</span>
          </div>
        </div>
      </div>
    </div>
  );
}
