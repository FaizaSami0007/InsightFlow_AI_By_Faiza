"use client";

import * as React from "react";
import Link from "next/link";
import { Activity, LogOut, Menu, Search, ShieldCheck, User as UserIcon } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dropdown } from "@/components/ui/dropdown";
import { useAuthStore } from "@/stores/use-auth-store";
import { useShellStore } from "@/stores/use-shell-store";

export function Header() {
  const { setMobileSidebarOpen, activeView } = useShellStore();
  const { user, isAuthenticated, logout } = useAuthStore();

  const viewTitles: Record<string, string> = {
    overview: "Platform Overview",
    datasets: "Datasets & Lineage",
    analytics: "Deterministic Analytics",
    ai: "AI Analyst Studio",
    dashboards: "Dashboards",
    settings: "System Configuration",
  };

  const userInitials = user?.full_name
    ? user.full_name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "US";

  return (
    <header className="sticky top-0 z-20 flex h-14 w-full items-center justify-between border-b border-border bg-surface/90 px-4 backdrop-blur-sm sm:px-6">
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
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-slate">Workspace</span>
          <span className="text-xs text-slate/60">/</span>
          <h1 className="text-sm font-semibold text-ink">
            {viewTitles[activeView] || "InsightFlow AI"}
          </h1>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Search Bar / Quick Command */}
        <div className="relative hidden sm:flex items-center">
          <div className="flex h-8 items-center gap-2 rounded-xl border border-border bg-cloud px-3 text-xs text-slate shadow-soft">
            <Search className="h-3.5 w-3.5 text-slate" />
            <span>Search datasets, queries...</span>
            <kbd className="rounded border border-border bg-surface px-1.5 py-0.5 text-[10px] font-semibold text-slate">
              Ctrl K
            </kbd>
          </div>
        </div>

        {/* System Health Badge */}
        <Badge variant="teal" dot className="text-[11px] font-medium hidden sm:inline-flex">
          <Activity className="h-3 w-3 mr-1" />
          API Online
        </Badge>

        {/* Security Indicator */}
        <div className="hidden lg:flex items-center gap-1.5 text-xs text-slate font-medium">
          <ShieldCheck className="h-4 w-4 text-teal" />
          <span className="text-[11px]">Allowlist Enforced</span>
        </div>

        {/* User Profile / Auth State */}
        <div className="flex items-center gap-2 border-l border-border pl-3">
          {isAuthenticated && user ? (
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
    </header>
  );
}
