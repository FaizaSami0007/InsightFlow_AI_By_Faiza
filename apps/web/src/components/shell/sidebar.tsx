"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  BookOpen,
  Bot,
  ChevronLeft,
  ChevronRight,
  Database,
  Layers,
  LayoutDashboard,
  LineChart,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  TrendingUp,
  Cpu,
  X,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useShellStore } from "@/stores/use-shell-store";

interface NavItemConfig {
  id: string;
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
}

const NAV_ITEMS: NavItemConfig[] = [
  { id: "overview", label: "Overview", href: "/", icon: Layers },
  { id: "datasets", label: "Datasets", href: "/datasets", icon: Database },
  { id: "collections", label: "Collections & Federation", href: "/collections", icon: Layers },
  { id: "connections", label: "Data Connections", href: "/connections", icon: Zap },
  { id: "analytics", label: "Analytics Engine", href: "/analytics", icon: LineChart },
  { id: "ai", label: "AI Analyst", href: "/analyst", icon: Bot },
  { id: "dashboards", label: "Dashboards", href: "/dashboards", icon: LayoutDashboard },
  { id: "forecast", label: "Forecasting", href: "/forecast", icon: TrendingUp },
  { id: "insights", label: "Insights & Anomalies", href: "/insights", icon: Zap },
  { id: "scenarios", label: "Scenarios & What-If", href: "/scenarios", icon: SlidersHorizontal },
  { id: "models", label: "Model Operations", href: "/models", icon: Cpu },
  { id: "knowledge", label: "Knowledge Center", href: "/knowledge", icon: BookOpen },
  { id: "security", label: "Security & Compliance", href: "/security", icon: ShieldCheck },
  { id: "observability", label: "Observability & Scaling", href: "/observability", icon: Activity },
];

export function Sidebar() {
  const pathname = usePathname();
  const {
    isSidebarExpanded,
    toggleSidebar,
    isMobileSidebarOpen,
    setMobileSidebarOpen,
    setActiveView,
  } = useShellStore();

  const navContent = (
    <div className="flex h-full flex-col justify-between p-3">
      <div>
        {/* Brand Header */}
        <div className="flex h-12 items-center justify-between px-2 pb-2">
          <Link
            href="/"
            className="flex items-center gap-2.5 overflow-hidden focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal rounded-xl"
            aria-label="InsightFlow AI Home"
          >
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-teal text-white shadow-soft">
              <Sparkles className="h-4 w-4" />
            </div>
            {isSidebarExpanded && (
              <div className="flex flex-col overflow-hidden leading-tight">
                <span className="truncate text-sm font-semibold text-ink tracking-tight">InsightFlow AI</span>
                <span className="truncate text-[10px] text-slate font-medium">Enterprise Analytics</span>
              </div>
            )}
          </Link>
          {/* Mobile close button */}
          <button
            onClick={() => setMobileSidebarOpen(false)}
            className="md:hidden rounded-lg p-1.5 text-slate hover:bg-cloud hover:text-ink focus-visible:ring-2 focus-visible:ring-teal"
            aria-label="Close navigation sidebar"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Navigation Section */}
        <nav className="mt-4 space-y-1" aria-label="Main Navigation">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive =
              item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);

            return (
              <Link
                key={item.id}
                href={item.href}
                onClick={() => {
                  setActiveView(item.id);
                  setMobileSidebarOpen(false);
                }}
                className={cn(
                  "flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-xs font-medium transition-all text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal",
                  isActive
                    ? "bg-teal-soft text-teal font-semibold border border-teal-border"
                    : "text-slate hover:bg-cloud hover:text-ink"
                )}
                title={!isSidebarExpanded ? item.label : undefined}
                aria-current={isActive ? "page" : undefined}
              >
                <Icon
                  className={cn(
                    "h-4 w-4 shrink-0 transition-colors",
                    isActive ? "text-teal" : "text-slate"
                  )}
                />
                {isSidebarExpanded && (
                  <span className="flex-1 truncate">{item.label}</span>
                )}
                {isSidebarExpanded && item.badge && (
                  <span
                    className={cn(
                      "rounded-md px-1.5 py-0.5 text-[10px] font-semibold",
                      isActive
                        ? "bg-teal text-white"
                        : "bg-cloud-subtle text-slate"
                    )}
                  >
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Sidebar Footer & Collapse Toggle */}
      <div className="space-y-2 border-t border-border pt-3">
        {isSidebarExpanded && (
          <div className="rounded-xl bg-cloud p-3 text-xs">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-teal animate-pulse" />
              <span className="font-semibold text-ink text-[11px]">Phase 2 Active</span>
            </div>
            <p className="mt-1 text-[11px] text-slate leading-tight">
              Identity & Ingestion Ready
            </p>
          </div>
        )}

        {/* Desktop Collapse Button */}
        <button
          onClick={toggleSidebar}
          className="hidden md:flex w-full items-center justify-center gap-2 rounded-xl border border-border bg-surface px-3 py-1.5 text-xs font-medium text-slate hover:bg-cloud hover:text-ink focus-visible:ring-2 focus-visible:ring-teal"
          aria-label={isSidebarExpanded ? "Collapse sidebar" : "Expand sidebar"}
        >
          {isSidebarExpanded ? (
            <>
              <ChevronLeft className="h-4 w-4" />
              <span>Collapse</span>
            </>
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
        </button>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop & Tablet Sidebar */}
      <aside
        className={cn(
          "hidden md:flex flex-col border-r border-border bg-surface transition-all duration-200 ease-in-out shrink-0 sticky top-0 h-screen z-30",
          isSidebarExpanded ? "w-64" : "w-18"
        )}
      >
        {navContent}
      </aside>

      {/* Mobile Drawer Backdrop and Sidebar */}
      {isMobileSidebarOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div
            className="fixed inset-0 bg-ink/40 backdrop-blur-[2px] transition-opacity"
            onClick={() => setMobileSidebarOpen(false)}
            aria-hidden="true"
          />
          <aside className="fixed inset-y-0 left-0 z-50 w-72 border-r border-border bg-surface shadow-soft-lg transition-transform">
            {navContent}
          </aside>
        </div>
      )}
    </>
  );
}
