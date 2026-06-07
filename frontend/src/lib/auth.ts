import { authApi } from './api';
import type { TokenResponse, User } from '@/types';

export const storeToken = (token: string): void => {
  if (typeof window !== 'undefined') {
    localStorage.setItem('access_token', token);
  }
};

export const getToken = (): string | null => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('access_token');
  }
  return null;
};

export const clearToken = (): void => {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('access_token');
    localStorage.removeItem('current_org_id');
  }
};

export const getStoredOrgId = (): string | null => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('current_org_id');
  }
  return null;
};

export const storeOrgId = (orgId: string): void => {
  if (typeof window !== 'undefined') {
    localStorage.setItem('current_org_id', orgId);
  }
};

export const isAuthenticated = (): boolean => {
  return getToken() !== null;
};
