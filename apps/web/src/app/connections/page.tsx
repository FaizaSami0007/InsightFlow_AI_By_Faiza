"use client";

import React from "react";
import { ConnectionWorkspace } from "@/components/connectors/connection-workspace";

export default function ConnectionsPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <ConnectionWorkspace />
    </div>
  );
}
