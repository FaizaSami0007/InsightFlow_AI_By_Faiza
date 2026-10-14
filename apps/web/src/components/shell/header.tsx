"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, LogOut, Menu, Search, ShieldCheck, User as UserIcon } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dropdown } from "@/components/ui/dropdown";
import { useAuthStore } from "@/stores/use-auth-store";
import { useShellStore } from "@/stores/use-shell-store";
import { CommandPalette } from "./command-palette";

const PATH_TITLES: Record<string, string> = {
  "/": "Platform Overview",
  "/datasets": "Datasets & Lineage",
  "/collections": "Collections & Federation",
  "/connections": "Data Connections",
  "/analytics": "Deterministic Analytics",
  "/analyst": "AI Analyst Studio",
  "/dashboards": "Dashboards",
  "/forecast": "Forecasting",
  "/insights": "Insights & Anomalies",
  "/scenarios": "Scenarios & What-If",
  "/models": "Model Operations",
  "/knowledge": "Knowledge Center",
  "/security": "Security & Compliance",
  "/observability": "Observability & Scaling",
  "/settings": "System Configuration",
  "/login": "Sign In",
  "/register": "Register",
};

function getHeaderTitle(pathname: string | null): string {
  if (!pathname) return "Platform Overview";
  if (PATH_TITLES[pathname]) return PATH_TITLES[pathname];
  for (const [route, title] of Object.entries(PATH_TITLES)) {
    if (route !== "/" && pathname.startsWith(route)) {
      return title;
    }
  }
  return "InsightFlow AI";
}

export function Header() {
  const pathname = usePathname();
  const { setMobileSidebarOpen, setIsSearchOpen } = useShellStore();
  const { user, isAuthenticated, logout } = useAuthStore();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  const activeTitle = getHeaderTitle(pathname);

  const userInitials = user?.full_name
    ? user.full_name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "US";

  return (
    <header className="sticky top-0 z-20 flex h-14 w-full items-center justify-between border-b border-border bg-surface/90 px-3 sm:px-6 backdrop-blur-sm gap-2 sm:gap-4">
      <div className="flex items-center gap-3">
        {/* Mobile menu trigger */}
        <button
          onClick={() => setMobileSidebarOpen(true)}
          className="rounded-xl border border-border p-2 text-slate hover:bg-cloud hover:text-ink md:hidden focus-visible:ring-2 focus-visible:ring-teal"
          aria-label="Open navigation menu"
        >
          <Menu className="h-4 w-4" />
        </button>

        {/* Current View & Breadcrumb */}
        <div className="flex items-center gap-1.5 sm:gap-2 min-w-0">
          <span className="text-xs font-medium text-slate hidden xs:inline">Workspace</span>
          <span className="text-xs text-slate/60 hidden xs:inline">/</span>
          <h1 className="text-xs sm:text-sm font-semibold text-ink truncate max-w-[130px] sm:max-w-xs md:max-w-sm lg:max-w-none">
            {activeTitle}
          </h1>
        </div>
      </div>

      <div className="flex items-center gap-2 sm:gap-3 shrink-0">
        {/* Mobile Search Button */}
        <button
          type="button"
          onClick={() => setIsSearchOpen(true)}
          className="flex h-8 w-8 items-center justify-center rounded-xl border border-border p-2 text-slate hover:bg-cloud hover:text-ink md:hidden focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal shrink-0"
          aria-label="Search across platform"
          title="Search (Ctrl + K)"
        >
          <Search className="h-4 w-4" />
        </button>

        {/* Search Bar / Quick Command Button */}
        <button
          type="button"
          onClick={() => setIsSearchOpen(true)}
          className="group relative hidden md:flex h-8 items-center justify-between gap-2 rounded-xl border border-border bg-cloud px-2.5 text-xs text-slate shadow-soft hover:border-teal-border hover:bg-surface hover:text-ink transition-all cursor-pointer shrink-0 w-36 sm:w-44 lg:w-60 xl:w-72 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal"
          aria-label="Open search and command palette"
          title="Search (Ctrl + K)"
        >
          <div className="flex items-center gap-2 min-w-0">
            <Search className="h-3.5 w-3.5 shrink-0 text-slate group-hover:text-teal transition-colors" />
            <span className="truncate text-slate group-hover:text-ink transition-colors text-left">
              <span className="hidden lg:inline">Search datasets, queries...</span>
              <span className="lg:hidden">Search...</span>
            </span>
          </div>
          <kbd className="inline-flex items-center shrink-0 whitespace-nowrap rounded border border-border bg-surface px-1.5 py-0.5 text-[10px] font-semibold text-slate group-hover:border-teal-border group-hover:text-teal transition-colors select-none leading-none">
            Ctrl K
          </kbd>
        </button>

        {/* System Health Badge */}
        <Badge variant="teal" dot className="text-[11px] font-medium hidden md:inline-flex shrink-0">
          <Activity className="h-3 w-3 mr-1" />
          API Online
        </Badge>

        {/* Security Indicator */}
        <div className="hidden xl:flex items-center gap-1.5 text-xs text-slate font-medium shrink-0">
          <ShieldCheck className="h-4 w-4 text-teal" />
          <span className="text-[11px]">Allowlist Enforced</span>
        </div>

        {/* User Profile / Auth State */}
        <div className="flex items-center gap-2 border-l border-border pl-3">
          {mounted && isAuthenticated && user ? (
            <Dropdown
              trigger={
                <button
                  className="flex items-center gap-2 rounded-xl p-1 text-left hover:bg-cloud focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal"
                  aria-label={`User menu for ${user.full_name}`}
                >
                  <div
                    className="flex h-8 w-8 items-center justify-center rounded-xl bg-teal-soft font-semibold text-teal text-xs border border-teal-border shadow-soft"
                    title={user.full_name}
                  >
                    {userInitials}
                  </div>
                  <div className="hidden xl:flex flex-col text-xs leading-tight pr-1">
                    <span className="font-semibold text-ink truncate max-w-[120px]">{user.full_name}</span>
                    <span className="text-[10px] text-slate truncate max-w-[120px]">{user.email}</span>
                  </div>
                </button>
              }
              items={[
                {
                  id: "profile",
                  label: `${user.full_name} (${user.email})`,
                  icon: <UserIcon className="h-3.5 w-3.5 text-slate" />,
                  onClick: () => {},
                  disabled: true,
                },
                {
                  id: "logout",
                  label: "Sign Out",
                  icon: <LogOut className="h-3.5 w-3.5 text-danger" />,
                  danger: true,
                  onClick: () => logout(),
                },
              ]}
            />
          ) : (
            <div className="flex items-center gap-2">
              <Link href="/login">
                <Button variant="ghost" size="sm">
                  Sign In
                </Button>
              </Link>
              <Link href="/register">
                <Button variant="primary" size="sm">
                  Register
                </Button>
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Global Command Palette & Search Modal */}
      <CommandPalette />
    </header>
  );
}
