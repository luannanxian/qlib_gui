/**
 * App Store
 *
 * Global state management for app-level settings:
 * - Theme (light/dark)
 * - Language (zh-CN/en-US)
 * - Sidebar collapsed state
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AppStore {
  // State
  theme: 'light' | 'dark';
  language: 'zh-CN' | 'en-US';
  sidebarCollapsed: boolean;

  // Actions
  toggleTheme: () => void;
  setLanguage: (lang: 'zh-CN' | 'en-US') => void;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
}

export const useAppStore = create<AppStore>()(
  persist(
    (set) => ({
      // Initial state
      theme: 'light',
      language: 'zh-CN',
      sidebarCollapsed: false,

      // Actions
      toggleTheme: () =>
        set((state) => ({
          theme: state.theme === 'light' ? 'dark' : 'light',
        })),

      setLanguage: (lang) => set({ language: lang }),

      toggleSidebar: () =>
        set((state) => ({
          sidebarCollapsed: !state.sidebarCollapsed,
        })),

      setSidebarCollapsed: (collapsed) =>
        set({ sidebarCollapsed: collapsed }),
    }),
    {
      name: 'app-storage', // localStorage key
    }
  )
);
