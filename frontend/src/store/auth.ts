'use client';

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '@/types';
import { clearToken, storeToken, storeOrgId } from '@/lib/auth';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  currentOrgId: string | null;
  isAuthenticated: boolean;
  hasHydrated: boolean;
  setAuth: (user: User, token: string, orgId?: string) => void;
  setHasHydrated: (hasHydrated: boolean) => void;
  setOrgId: (orgId: string) => void;
  logout: () => void;
}

const getOrgIdFromToken = (token: string): string | null => {
  if (typeof window === 'undefined') return null;
  try {
    const payload = token.split('.')[1];
    if (!payload) return null;
    const normalized = payload.replace(/-/g, '+').replace(/_/g, '/');
    const padded = normalized.padEnd(normalized.length + ((4 - (normalized.length % 4)) % 4), '=');
    const decoded = JSON.parse(window.atob(padded)) as { org_id?: string };
    return decoded.org_id ?? null;
  } catch {
    return null;
  }
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      currentOrgId: null,
      isAuthenticated: false,
      hasHydrated: false,

      setAuth: (user, token, orgId) => {
        const resolvedOrgId = orgId ?? getOrgIdFromToken(token);
        storeToken(token);
        if (resolvedOrgId) storeOrgId(resolvedOrgId);
        set({ user, accessToken: token, currentOrgId: resolvedOrgId, isAuthenticated: true });
      },

      setOrgId: (orgId) => {
        storeOrgId(orgId);
        set({ currentOrgId: orgId });
      },

      setHasHydrated: (hasHydrated) => {
        set({ hasHydrated });
      },

      logout: () => {
        clearToken();
        set({ user: null, accessToken: null, currentOrgId: null, isAuthenticated: false });
      },
    }),
    {
      name: 'auth-storage',
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
      },
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        currentOrgId: state.currentOrgId,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
