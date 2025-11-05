/**
 * User Store
 *
 * Global state management for user-related data:
 * - User ID
 * - User mode (BEGINNER/EXPERT)
 * - User preferences
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { UserMode, PreferencesResponse } from '@/types/api';

interface UserStore {
  // State
  userId: string | null;
  mode: UserMode;
  preferences: PreferencesResponse | null;

  // Actions
  setUserId: (id: string) => void;
  setMode: (mode: UserMode) => void;
  setPreferences: (prefs: PreferencesResponse) => void;
  reset: () => void;
}

const initialState = {
  userId: null,
  mode: 'BEGINNER' as UserMode,
  preferences: null,
};

export const useUserStore = create<UserStore>()(
  persist(
    (set) => ({
      ...initialState,

      setUserId: (id: string) => set({ userId: id }),

      setMode: (mode: UserMode) => set({ mode }),

      setPreferences: (prefs: PreferencesResponse) =>
        set({ preferences: prefs, mode: prefs.mode }),

      reset: () => set(initialState),
    }),
    {
      name: 'user-storage', // localStorage key
      partialize: (state) => ({
        userId: state.userId,
        mode: state.mode,
        // Don't persist full preferences to localStorage
      }),
    }
  )
);
