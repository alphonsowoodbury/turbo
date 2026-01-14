"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

export type MobileTab = "home" | "tasks" | "create" | "chat" | "more";

interface MobileNavState {
  // Drawer state
  isDrawerOpen: boolean;
  openDrawer: () => void;
  closeDrawer: () => void;
  toggleDrawer: () => void;

  // Active tab (for bottom nav highlighting)
  activeTab: MobileTab;
  setActiveTab: (tab: MobileTab) => void;

  // Expanded menu sections in drawer
  expandedSections: string[];
  toggleSection: (section: string) => void;
}

export const useMobileNav = create<MobileNavState>()(
  persist(
    (set) => ({
      // Drawer
      isDrawerOpen: false,
      openDrawer: () => set({ isDrawerOpen: true }),
      closeDrawer: () => set({ isDrawerOpen: false }),
      toggleDrawer: () => set((state) => ({ isDrawerOpen: !state.isDrawerOpen })),

      // Active tab
      activeTab: "home",
      setActiveTab: (tab) => set({ activeTab: tab, isDrawerOpen: false }),

      // Expanded sections
      expandedSections: ["projects"],
      toggleSection: (section) =>
        set((state) => ({
          expandedSections: state.expandedSections.includes(section)
            ? state.expandedSections.filter((s) => s !== section)
            : [...state.expandedSections, section],
        })),
    }),
    {
      name: "mobile-nav-storage",
      partialize: (state) => ({
        activeTab: state.activeTab,
        expandedSections: state.expandedSections,
      }),
    }
  )
);
