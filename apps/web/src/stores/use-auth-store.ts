"use client";

import { create } from "zustand";
import { api, ApiError } from "@/lib/api-client";
import { TokenResponse, User } from "@/types";

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isInitializing: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<boolean>;
  register: (email: string, password: string, fullName: string) => Promise<boolean>;
  logout: () => void;
  initializeAuth: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: false,
  isInitializing: true,
  error: null,

  clearError: () => set({ error: null }),

  initializeAuth: async () => {
    if (typeof window === "undefined") {
      set({ isInitializing: false });
      return;
    }

    const savedToken = localStorage.getItem("insightflow_auth_token");
    if (!savedToken) {
      set({ user: null, token: null, isAuthenticated: false, isInitializing: false });
      return;
    }

    set({ token: savedToken, isLoading: true });

    try {
      const user = await api.get<User>("/api/v1/auth/me");
      set({ user, token: savedToken, isAuthenticated: true, isLoading: false, isInitializing: false, error: null });
    } catch {
      // Stale or invalid token
      localStorage.removeItem("insightflow_auth_token");
      set({ user: null, token: null, isAuthenticated: false, isLoading: false, isInitializing: false });
    }
  },

  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.post<TokenResponse>("/api/v1/auth/login", { email, password });
      if (typeof window !== "undefined") {
        localStorage.setItem("insightflow_auth_token", response.access_token);
      }
      set({
        user: response.user,
        token: response.access_token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
      return true;
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Unable to sign in. Please verify your credentials.";
      set({ error: message, isLoading: false, isAuthenticated: false });
      return false;
    }
  },

  register: async (email: string, password: string, fullName: string) => {
    set({ isLoading: true, error: null });
    try {
      // 1. Create account
      await api.post<User>("/api/v1/auth/register", {
        email,
        password,
        full_name: fullName,
      });
      // 2. Automatically authenticate
      const success = await get().login(email, password);
      return success;
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Registration failed. Please check your information.";
      set({ error: message, isLoading: false });
      return false;
    }
  },

  logout: async () => {
    try {
      if (get().token) {
        await api.post("/api/v1/auth/logout");
      }
    } catch {
      // Ignore network errors on logout
    } finally {
      if (typeof window !== "undefined") {
        localStorage.removeItem("insightflow_auth_token");
      }
      set({ user: null, token: null, isAuthenticated: false, error: null });
    }
  },
}));
