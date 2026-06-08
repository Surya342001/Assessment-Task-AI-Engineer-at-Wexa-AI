import axios, { AxiosError } from 'axios';
import type {
  Alert,
  AlertHistory,
  APIKey,
  ChartDataPoint,
  Dashboard,
  Event,
  Member,
  Organization,
  TokenResponse,
  Widget,
} from '@/types';

const API_ORIGIN = (process.env.NEXT_PUBLIC_API_URL || '').replace(/\/$/, '');
const API_PREFIX = `${API_ORIGIN}/api`;

export const apiClient = axios.create({
  baseURL: API_PREFIX,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true, // For refresh token cookie
});

// Request interceptor: attach JWT
apiClient.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Response interceptor: handle 401 & refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as typeof error.config & { _retry?: boolean };
    const requestUrl = original?.url ?? '';
    const isAuthEndpoint = ['/auth/signin', '/auth/signup', '/auth/refresh'].some((path) =>
      requestUrl.includes(path)
    );

    if (error.response?.status === 401 && original && !original._retry && !isAuthEndpoint) {
      original._retry = true;
      try {
        const { data } = await axios.post<TokenResponse>(
          `${API_PREFIX}/auth/refresh`,
          {},
          { withCredentials: true }
        );
        localStorage.setItem('access_token', data.access_token);
        original.headers = original.headers || {};
        original.headers.Authorization = `Bearer ${data.access_token}`;
        return apiClient(original);
      } catch {
        localStorage.removeItem('access_token');
        if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

// ──────────────── Auth ────────────────
export const authApi = {
  signUp: (data: { email: string; password: string; full_name: string; organization_name: string }) =>
    apiClient.post<TokenResponse>('/auth/signup', data),
  signIn: (data: { email: string; password: string }) =>
    apiClient.post<TokenResponse>('/auth/signin', data),
  refresh: () => apiClient.post<TokenResponse>('/auth/refresh'),
  logout: () => apiClient.post('/auth/logout'),
  me: () => apiClient.get('/auth/me'),
};

// ──────────────── Organizations ────────────────
export const orgApi = {
  create: (data: { name: string }) => apiClient.post<Organization>('/orgs/', data),
  get: (orgId: string) => apiClient.get<Organization>(`/orgs/${orgId}`),
  update: (orgId: string, data: Partial<Organization>) =>
    apiClient.patch<Organization>(`/orgs/${orgId}`, data),
  listMembers: (orgId: string) => apiClient.get<Member[]>(`/orgs/${orgId}/members`),
  inviteMember: (orgId: string, data: { email: string; role: string }) =>
    apiClient.post(`/orgs/${orgId}/members/invite`, data),
  acceptInvitation: (token: string) =>
    apiClient.post(`/orgs/invitations/${token}/accept`),
  updateMemberRole: (orgId: string, userId: string, role: string) =>
    apiClient.patch(`/orgs/${orgId}/members/${userId}/role`, { role }),
  removeMember: (orgId: string, userId: string) =>
    apiClient.delete(`/orgs/${orgId}/members/${userId}`),
};

// ──────────────── Events ────────────────
export const eventsApi = {
  ingestSingle: (
    orgId: string,
    event: {
      name: string;
      properties: Record<string, unknown>;
      timestamp?: string;
      session_id?: string;
      user_id?: string;
    }
  ) =>
    apiClient.post(`/orgs/${orgId}/events/ingest`, event),
  ingestBatch: (orgId: string, events: unknown[]) =>
    apiClient.post(`/orgs/${orgId}/events/ingest/batch`, { events }),
  list: (orgId: string, params?: { limit?: number; offset?: number }) =>
    apiClient.get<Event[]>(`/orgs/${orgId}/events/`, { params }),
  aggregate: (orgId: string, params: unknown) =>
    apiClient.post<ChartDataPoint[]>(`/orgs/${orgId}/events/aggregate`, params),
};

// ──────────────── Dashboards ────────────────
export const dashboardsApi = {
  list: (orgId: string) => apiClient.get<Dashboard[]>(`/orgs/${orgId}/dashboards/`),
  create: (orgId: string, data: Partial<Dashboard>) =>
    apiClient.post<Dashboard>(`/orgs/${orgId}/dashboards/`, data),
  get: (orgId: string, dashboardId: string) =>
    apiClient.get<Dashboard>(`/orgs/${orgId}/dashboards/${dashboardId}`),
  update: (orgId: string, dashboardId: string, data: Partial<Dashboard>) =>
    apiClient.patch<Dashboard>(`/orgs/${orgId}/dashboards/${dashboardId}`, data),
  delete: (orgId: string, dashboardId: string) =>
    apiClient.delete(`/orgs/${orgId}/dashboards/${dashboardId}`),
  share: (orgId: string, dashboardId: string) =>
    apiClient.post<{ public_slug: string; public_url: string }>(
      `/orgs/${orgId}/dashboards/${dashboardId}/share`
    ),
  unshare: (orgId: string, dashboardId: string) =>
    apiClient.delete(`/orgs/${orgId}/dashboards/${dashboardId}/share`),
  getPublic: (slug: string) => apiClient.get<Dashboard>(`/public/dashboards/${slug}`),
  addWidget: (orgId: string, dashboardId: string, data: Partial<Widget>) =>
    apiClient.post<Widget>(`/orgs/${orgId}/dashboards/${dashboardId}/widgets`, data),
  updateWidget: (orgId: string, dashboardId: string, widgetId: string, data: Partial<Widget>) =>
    apiClient.patch<Widget>(`/orgs/${orgId}/dashboards/${dashboardId}/widgets/${widgetId}`, data),
  deleteWidget: (orgId: string, dashboardId: string, widgetId: string) =>
    apiClient.delete(`/orgs/${orgId}/dashboards/${dashboardId}/widgets/${widgetId}`),
};

// ──────────────── Alerts ────────────────
export const alertsApi = {
  list: (orgId: string) => apiClient.get<Alert[]>(`/orgs/${orgId}/alerts/`),
  create: (orgId: string, data: Partial<Alert>) =>
    apiClient.post<Alert>(`/orgs/${orgId}/alerts/`, data),
  get: (orgId: string, alertId: string) =>
    apiClient.get<Alert>(`/orgs/${orgId}/alerts/${alertId}`),
  update: (orgId: string, alertId: string, data: Partial<Alert>) =>
    apiClient.patch<Alert>(`/orgs/${orgId}/alerts/${alertId}`, data),
  delete: (orgId: string, alertId: string) =>
    apiClient.delete(`/orgs/${orgId}/alerts/${alertId}`),
  mute: (orgId: string, alertId: string, duration_minutes: number) =>
    apiClient.post<Alert>(`/orgs/${orgId}/alerts/${alertId}/mute`, { duration_minutes }),
  unmute: (orgId: string, alertId: string) =>
    apiClient.post<Alert>(`/orgs/${orgId}/alerts/${alertId}/unmute`),
  history: (orgId: string, alertId: string) =>
    apiClient.get<AlertHistory[]>(`/orgs/${orgId}/alerts/${alertId}/history`),
};

// ──────────────── API Keys ────────────────
export const apiKeysApi = {
  list: (orgId: string) => apiClient.get<APIKey[]>(`/orgs/${orgId}/api-keys/`),
  create: (orgId: string, data: { name: string }) =>
    apiClient.post<APIKey & { key: string }>(`/orgs/${orgId}/api-keys/`, data),
  revoke: (orgId: string, keyId: string) =>
    apiClient.delete(`/orgs/${orgId}/api-keys/${keyId}`),
};
