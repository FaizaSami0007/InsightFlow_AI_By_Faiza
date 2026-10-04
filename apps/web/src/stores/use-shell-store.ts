import { create } from "zustand";

interface ShellState {
  isSidebarExpanded: boolean;
  isMobileSidebarOpen: boolean;
  activeView: string;
  activeDatasetId: string | null;
  toggleSidebar: () => void;
  setSidebarExpanded: (expanded: boolean) => void;
  setMobileSidebarOpen: (open: boolean) => void;
  setActiveView: (view: string) => void;
  setActiveDatasetId: (id: string | null) => void;
}

export const useShellStore = create<ShellState>((set) => ({
  isSidebarExpanded: true,
  isMobileSidebarOpen: false,
  activeView: "overview",
  activeDatasetId: null,
  toggleSidebar: () => set((state) => ({ isSidebarExpanded: !state.isSidebarExpanded })),
  setSidebarExpanded: (expanded) => set({ isSidebarExpanded: expanded }),
  setMobileSidebarOpen: (open) => set({ isMobileSidebarOpen: open }),
  setActiveView: (view) => set({ activeView: view }),
  setActiveDatasetId: (id) => set({ activeDatasetId: id }),
}));
