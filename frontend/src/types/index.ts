export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  owner_id: string;
  created_at: string;
}

export interface Member {
  id: string;
  user_id: string;
  role: UserRole;
  joined_at: string;
  user: { id: string; email: string; full_name: string };
}

export type UserRole = 'owner' | 'admin' | 'analyst' | 'viewer';

export interface Event {
  id: string;
  organization_id: string;
  name: string;
  properties: Record<string, unknown>;
  timestamp: string;
  source: 'api' | 'csv' | 'webhook';
  session_id: string | null;
  user_id: string | null;
  ingested_at: string;
}

export type WidgetType = 'line_chart' | 'bar_chart' | 'pie_chart' | 'kpi_card' | 'table';

export interface WidgetPosition {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface QueryConfig {
  event_name: string;
  aggregation: string;
  property_key?: string;
  group_by?: string;
  filters: Record<string, unknown>;
  time_range: string;
  interval: string;
}

export interface Widget {
  id: string;
  dashboard_id: string;
  widget_type: WidgetType;
  title: string;
  query_config: QueryConfig;
  position: WidgetPosition;
  options: Record<string, unknown>;
  created_at: string;
}

export interface Dashboard {
  id: string;
  organization_id: string;
  name: string;
  description: string | null;
  layout: unknown[];
  is_public: boolean;
  public_slug: string | null;
  refresh_interval: number | null;
  created_by_id: string | null;
  created_at: string;
  updated_at: string;
  widgets: Widget[];
}

export type AlertStatus = 'active' | 'triggered' | 'resolved' | 'muted';
export type AlertCondition = 'gt' | 'lt' | 'gte' | 'lte' | 'eq';

export interface Alert {
  id: string;
  organization_id: string;
  name: string;
  description: string | null;
  metric_query: QueryConfig;
  condition: AlertCondition;
  threshold: number;
  window_minutes: number;
  status: AlertStatus;
  notification_channels: NotificationChannel[];
  muted_until: string | null;
  last_evaluated_at: string | null;
  created_by_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface AlertHistory {
  id: string;
  alert_id: string;
  triggered_at: string;
  resolved_at: string | null;
  triggered_value: number;
  message: string;
}

export interface NotificationChannel {
  type: 'email' | 'webhook' | 'in_app';
  config: Record<string, string>;
}

export interface APIKey {
  id: string;
  name: string;
  key_prefix: string;
  is_active: boolean;
  last_used_at: string | null;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface ChartDataPoint {
  bucket: string;
  value: number;
  group_key?: string;
}

// WebSocket message types
export type WSMessage =
  | { type: 'connected'; org_id: string; message: string }
  | { type: 'new_events'; org_id: string; event_ids: string[]; count: number }
  | { type: 'alert_triggered'; alert_id: string; message: string }
  | { type: 'pong' }
  | { type: 'heartbeat' };
