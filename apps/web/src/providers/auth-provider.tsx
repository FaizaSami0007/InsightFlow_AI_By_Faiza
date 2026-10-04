"use client";

import * as React from "react";
import { useAuthStore } from "@/stores/use-auth-store";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const initializeAuth = useAuthStore((state) => state.initializeAuth);

  React.useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  return <>{children}</>;
}
