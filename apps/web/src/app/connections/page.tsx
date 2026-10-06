"use client";

import React from "react";
import { AppShell } from "@/components/shell/app-shell";
import { ConnectionWorkspace } from "@/components/connectors/connection-workspace";

export default function ConnectionsPage() {
  return (
    <AppShell>
      <ConnectionWorkspace />
    </AppShell>
  );
}
