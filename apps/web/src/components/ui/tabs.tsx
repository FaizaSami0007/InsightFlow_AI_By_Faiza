"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface TabsContextValue {
  activeTab: string;
  setActiveTab: (value: string) => void;
}

const TabsContext = React.createContext<TabsContextValue | null>(null);

export function Tabs({
  value,
  defaultValue,
  onValueChange,
  children,
  className,
}: {
  value?: string;
  defaultValue?: string;
  onValueChange?: (val: string) => void;
  children: React.ReactNode;
  className?: string;
}) {
  const [internalTab, setInternalTab] = React.useState(defaultValue || "");
  const activeTab = value !== undefined ? value : internalTab;

  const handleTabChange = (val: string) => {
    if (value === undefined) {
      setInternalTab(val);
    }
    onValueChange?.(val);
  };

  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab: handleTabChange }}>
      <div className={cn("w-full space-y-4", className)}>{children}</div>
    </TabsContext.Provider>
  );
}

export function TabList({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div
      role="tablist"
      className={cn(
        "inline-flex items-center gap-1 rounded-xl border border-border bg-cloud p-1 text-slate max-w-full overflow-x-auto scrollbar-none",
        className
      )}
    >
      {children}
    </div>
  );
}

export function TabTrigger({
  value,
  children,
  className,
  disabled,
}: {
  value: string;
  children: React.ReactNode;
  className?: string;
  disabled?: boolean;
}) {
  const context = React.useContext(TabsContext);
  if (!context) throw new Error("TabTrigger must be used inside Tabs");

  const isSelected = context.activeTab === value;

  return (
    <button
      role="tab"
      aria-selected={isSelected}
      disabled={disabled}
      onClick={() => context.setActiveTab(value)}
      className={cn(
        "inline-flex items-center justify-center shrink-0 whitespace-nowrap rounded-lg px-3.5 py-1.5 text-xs font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal",
        isSelected
          ? "bg-surface text-ink font-semibold shadow-soft"
          : "text-slate hover:text-ink hover:bg-surface/50",
        disabled && "opacity-50 cursor-not-allowed",
        className
      )}
    >
      {children}
    </button>
  );
}

export function TabContent({
  value,
  children,
  className,
}: {
  value: string;
  children: React.ReactNode;
  className?: string;
}) {
  const context = React.useContext(TabsContext);
  if (!context) throw new Error("TabContent must be used inside Tabs");

  if (context.activeTab !== value) return null;

  return (
    <div role="tabpanel" className={cn("focus-visible:outline-none", className)}>
      {children}
    </div>
  );
}

export const TabsList = TabList;
export const TabsTrigger = TabTrigger;
export const TabsContent = TabContent;

