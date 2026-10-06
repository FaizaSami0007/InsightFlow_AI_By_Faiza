"use client";

import * as React from "react";
import { Sidebar } from "./sidebar";
import { Header } from "./header";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen bg-cloud text-ink font-sans selection:bg-teal-soft selection:text-teal">
      {/* Skip to Content accessible link for screen readers and keyboard users */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:rounded-xl focus:bg-teal focus:px-4 focus:py-2 focus:text-xs focus:font-semibold focus:text-white focus:shadow-soft-lg focus:outline-none"
      >
        Skip to main content
      </a>

      {/* Navigation Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-x-hidden min-w-0">
        <Header />
        <main
          id="main-content"
          tabIndex={-1}
          className="flex-1 overflow-y-auto overflow-x-hidden px-3 py-4 sm:px-6 sm:py-6 lg:px-8 lg:py-8 focus:outline-none"
        >
          <div className="mx-auto max-w-7xl w-full">{children}</div>
        </main>
      </div>
    </div>
  );
}
