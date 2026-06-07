'use client';

import { useMemo, useState, type ReactNode } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart as RechartsPieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import Link from 'next/link';
import toast from 'react-hot-toast';
import {
  Activity,
  BarChart3,
  Clock3,
  Database,
  PieChart,
  Plus,
  RadioTower,
  Send,
  Trash2,
  TrendingUp,
  Users,
  type LucideIcon,
} from 'lucide-react';
import { dashboardsApi, eventsApi } from '@/lib/api';
import { useAuthStore } from '@/store/auth';
import { formatDate, formatNumber, formatRelativeDate } from '@/lib/utils';
import type { Dashboard, Event } from '@/types';

const chartColors = ['#60a5fa', '#34d399', '#f59e0b', '#f472b6', '#a78bfa', '#22d3ee'];

const eventTemplates = [
  { name: 'page_view', properties: { page: '/dashboard/dashboards', referrer: 'dashboard-demo' } },
  { name: 'button_click', properties: { button: 'new_dashboard', component: 'dashboards' } },
  { name: 'report_exported', properties: { format: 'pdf', report: 'executive_overview' } },
  { name: 'alert_checked', properties: { severity: 'high', status: 'investigated' } },
];

type CountDatum = {
  name: string;
  value: number;
  fill: string;
  percentage: number;
};

type SourceDatum = {
  source: string;
  events: number;
  fill: string;
};

type TimelineDatum = {
  time: string;
  events: number;
};

type UserDatum = {
  user: string;
  events: number;
};

function createInjectedDashboardEvent() {
  const template = eventTemplates[Math.floor(Math.random() * eventTemplates.length)];

  return {
    name: template.name,
    session_id: `dashboard-session-${Date.now()}`,
    user_id: 'demo-dashboard-user',
    timestamp: new Date().toISOString(),
    properties: {
      ...template.properties,
      injected_from: 'dashboards_page',
      assignment_demo: true,
      value: Math.floor(Math.random() * 900) + 100,
      browser_path: typeof window !== 'undefined' ? window.location.pathname : '/dashboard/dashboards',
    },
  };
}

function buildCountData(events: Event[], getLabel: (event: Event) => string): CountDatum[] {
  const counts = new Map<string, number>();

  events.forEach((event) => {
    const label = getLabel(event) || 'unknown';
    counts.set(label, (counts.get(label) ?? 0) + 1);
  });

  const total = events.length || 1;

  return Array.from(counts.entries())
    .sort((first, second) => second[1] - first[1])
    .slice(0, 6)
    .map(([name, value], index) => ({
      name,
      value,
      fill: chartColors[index % chartColors.length],
      percentage: Math.round((value / total) * 100),
    }));
}

function buildTimelineData(events: Event[]): TimelineDatum[] {
  const buckets = new Map<string, { label: string; sortValue: number; events: number }>();

  events.forEach((event) => {
    const eventDate = new Date(event.timestamp);
    if (Number.isNaN(eventDate.getTime())) return;

    eventDate.setMinutes(0, 0, 0);
    const sortValue = eventDate.getTime();
    const label = eventDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const existing = buckets.get(String(sortValue));

    buckets.set(String(sortValue), {
      label,
      sortValue,
      events: (existing?.events ?? 0) + 1,
    });
  });

  return Array.from(buckets.values())
    .sort((first, second) => first.sortValue - second.sortValue)
    .slice(-10)
    .map((bucket) => ({ time: bucket.label, events: bucket.events }));
}

function buildSourceData(events: Event[]): SourceDatum[] {
  return buildCountData(events, (event) => event.source).map((datum) => ({
    source: datum.name,
    events: datum.value,
    fill: datum.fill,
  }));
}

function buildUserData(events: Event[]): UserDatum[] {
  return buildCountData(events, (event) => event.user_id || 'anonymous')
    .slice(0, 5)
    .map((datum) => ({ user: datum.name, events: datum.value }));
}

function getDemoEventCount(events: Event[]) {
  return events.filter((event) => event.properties?.assignment_demo === true).length;
}

export default function DashboardsPage() {
  const { currentOrgId } = useAuthStore();
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');

  const { data: dashboards = [], isLoading: dashboardsLoading } = useQuery({
    queryKey: ['dashboards', currentOrgId],
    queryFn: () =>
      currentOrgId
        ? dashboardsApi.list(currentOrgId).then((response) => response.data)
        : Promise.resolve([]),
    enabled: !!currentOrgId,
  });

  const { data: events = [], isLoading: eventsLoading, refetch: refetchEvents } = useQuery({
    queryKey: ['events', currentOrgId, 'dashboard-analytics'],
    queryFn: () =>
      currentOrgId
        ? eventsApi.list(currentOrgId, { limit: 100 }).then((response) => response.data)
        : Promise.resolve([]),
    enabled: !!currentOrgId,
    refetchInterval: 10_000,
  });

  const createMutation = useMutation({
    mutationFn: () =>
      dashboardsApi.create(currentOrgId!, { name: newName.trim() }).then((response) => response.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboards', currentOrgId] });
      setShowCreate(false);
      setNewName('');
      toast.success('Dashboard created');
    },
    onError: () => toast.error('Could not create dashboard'),
  });

  const deleteMutation = useMutation({
    mutationFn: (dashboardId: string) => dashboardsApi.delete(currentOrgId!, dashboardId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboards', currentOrgId] });
      toast.success('Dashboard deleted');
    },
    onError: () => toast.error('Could not delete dashboard'),
  });

  const injectEvent = useMutation({
    mutationFn: async () => {
      if (!currentOrgId) throw new Error('Organization is not ready yet');
      return eventsApi.ingestSingle(currentOrgId, createInjectedDashboardEvent());
    },
    onSuccess: async () => {
      toast.success('Dashboard event injected');
      await queryClient.invalidateQueries({ queryKey: ['events', currentOrgId] });
      await refetchEvents();
    },
    onError: () => toast.error('Could not inject event'),
  });

  const eventTypeData = useMemo(() => buildCountData(events, (event) => event.name), [events]);
  const sourceData = useMemo(() => buildSourceData(events), [events]);
  const timelineData = useMemo(() => buildTimelineData(events), [events]);
  const topUsers = useMemo(() => buildUserData(events), [events]);
  const recentEvents = useMemo(() => events.slice(0, 8), [events]);
  const uniqueUsers = useMemo(
    () => new Set(events.map((event) => event.user_id).filter(Boolean)).size,
    [events]
  );
  const demoEvents = useMemo(() => getDemoEventCount(events), [events]);
  const latestEvent = events[0];
  const hasEvents = events.length > 0;
  const canCreateDashboard = newName.trim().length > 0 && !createMutation.isPending;

  return (
    <div className="min-h-full p-6 text-slate-100 lg:p-8">
      <div className="mb-8 flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
        <div className="max-w-3xl">
          <p className="section-label">Event intelligence</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-white">Dashboards</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-200">
            Monitor event volume, source mix, active users, and the newest payloads from one live analytics surface.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => injectEvent.mutate()}
            disabled={!currentOrgId || injectEvent.isPending}
            className="btn-secondary border-cyan-400/30 bg-cyan-400/10 text-cyan-100 hover:border-cyan-300/50 hover:bg-cyan-400/15 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <Send size={16} />
            {injectEvent.isPending ? 'Injecting...' : 'Inject Event'}
          </button>
          <button onClick={() => setShowCreate(true)} className="btn-primary">
            <Plus size={16} />
            New Dashboard
          </button>
        </div>
      </div>

      {showCreate && (
        <div className="mb-6 flex flex-col gap-3 rounded-2xl border border-slate-700/70 bg-slate-900/85 p-4 shadow-2xl shadow-black/20 md:flex-row">
          <input
            className="input flex-1 border-slate-700 bg-slate-950/80 text-slate-100 placeholder:text-slate-300"
            placeholder="Dashboard name"
            value={newName}
            onChange={(event) => setNewName(event.target.value)}
            onKeyDown={(event) => event.key === 'Enter' && canCreateDashboard && createMutation.mutate()}
            autoFocus
          />
          <button
            onClick={() => createMutation.mutate()}
            disabled={!canCreateDashboard}
            className="btn-primary"
          >
            Create
          </button>
          <button onClick={() => setShowCreate(false)} className="btn-secondary border-slate-700 bg-slate-900 text-slate-300">
            Cancel
          </button>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          icon={Database}
          label="Total events"
          value={formatNumber(events.length)}
          detail={hasEvents ? 'Last 100 events loaded' : 'Waiting for ingestion'}
          accent="from-blue-500 to-cyan-400"
        />
        <MetricCard
          icon={PieChart}
          label="Event types"
          value={formatNumber(eventTypeData.length)}
          detail={eventTypeData[0] ? `${eventTypeData[0].name} leads at ${eventTypeData[0].percentage}%` : 'No event mix yet'}
          accent="from-emerald-400 to-teal-300"
        />
        <MetricCard
          icon={Users}
          label="Active users"
          value={formatNumber(uniqueUsers)}
          detail={uniqueUsers ? 'Known user/session activity' : 'Anonymous traffic only'}
          accent="from-amber-400 to-orange-300"
        />
        <MetricCard
          icon={Clock3}
          label="Latest event"
          value={latestEvent ? formatRelativeDate(latestEvent.timestamp) : 'No data'}
          detail={latestEvent?.name ?? 'Inject an event to start'}
          accent="from-fuchsia-400 to-rose-300"
        />
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-[0.9fr_1.3fr]">
        <ChartPanel title="Event type mix" description="Pie chart breakdown by event name" icon={PieChart} action={`${formatNumber(demoEvents)} demo events`}>
          {eventTypeData.length > 0 ? (
            <div className="grid gap-5 lg:grid-cols-[220px_1fr] lg:items-center">
              <div className="h-[240px] min-w-0">
                <ResponsiveContainer width="100%" height="100%">
                  <RechartsPieChart>
                    <Pie data={eventTypeData} dataKey="value" nameKey="name" innerRadius={62} outerRadius={96} paddingAngle={4} stroke="rgba(15, 23, 42, 0.95)" strokeWidth={4}>
                      {eventTypeData.map((datum) => <Cell key={datum.name} fill={datum.fill} />)}
                    </Pie>
                    <Tooltip
                      contentStyle={{ background: '#0f172a', border: '1px solid rgba(148, 163, 184, 0.35)', borderRadius: 12, color: '#e2e8f0' }}
                      itemStyle={{ color: '#e2e8f0' }}
                      labelStyle={{ color: '#bfdbfe', fontWeight: 700 }}
                    />
                  </RechartsPieChart>
                </ResponsiveContainer>
              </div>
              <div className="space-y-3">
                {eventTypeData.map((datum) => (
                  <div key={datum.name} className="flex items-center gap-3 rounded-xl border border-slate-700/60 bg-slate-950/40 p-3">
                    <span className="h-3 w-3 rounded-full" style={{ backgroundColor: datum.fill }} />
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-mono text-xs text-slate-200">{datum.name}</p>
                      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-800">
                        <div className="h-full rounded-full" style={{ width: `${datum.percentage}%`, backgroundColor: datum.fill }} />
                      </div>
                    </div>
                    <span className="text-sm font-semibold text-white">{datum.percentage}%</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <EmptyAnalyticsState onInject={() => injectEvent.mutate()} isPending={injectEvent.isPending} />
          )}
        </ChartPanel>

        <ChartPanel title="Event throughput" description="Hourly activity from the latest event stream" icon={TrendingUp} action="Auto-refresh 10s">
          {timelineData.length > 0 ? (
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={timelineData} margin={{ left: 4, right: 18, top: 12, bottom: 0 }}>
                  <defs>
                    <linearGradient id="throughputFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#60a5fa" stopOpacity={0.45} />
                      <stop offset="95%" stopColor="#22d3ee" stopOpacity={0.03} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="rgba(148, 163, 184, 0.12)" vertical={false} />
                  <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{ fill: '#cbd5e1', fontSize: 12, fontWeight: 600 }} />
                  <YAxis allowDecimals={false} axisLine={false} tickLine={false} tick={{ fill: '#cbd5e1', fontSize: 12, fontWeight: 600 }} width={34} />
                  <Tooltip
                    contentStyle={{ background: '#0f172a', border: '1px solid rgba(148, 163, 184, 0.35)', borderRadius: 12, color: '#e2e8f0' }}
                    itemStyle={{ color: '#e2e8f0' }}
                    labelStyle={{ color: '#bfdbfe', fontWeight: 700 }}
                  />
                  <Area type="monotone" dataKey="events" stroke="#60a5fa" strokeWidth={3} fill="url(#throughputFill)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <EmptyAnalyticsState onInject={() => injectEvent.mutate()} isPending={injectEvent.isPending} />
          )}
        </ChartPanel>
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <ChartPanel title="Traffic sources" description="Graphical source distribution" icon={RadioTower} action="API / CSV / webhook">
          {sourceData.length > 0 ? (
            <div className="h-[260px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={sourceData} margin={{ left: 2, right: 12, top: 10, bottom: 0 }}>
                  <CartesianGrid stroke="rgba(148, 163, 184, 0.12)" vertical={false} />
                  <XAxis dataKey="source" axisLine={false} tickLine={false} tick={{ fill: '#cbd5e1', fontSize: 12, fontWeight: 600 }} />
                  <YAxis allowDecimals={false} axisLine={false} tickLine={false} tick={{ fill: '#cbd5e1', fontSize: 12, fontWeight: 600 }} width={34} />
                  <Tooltip
                    contentStyle={{ background: '#0f172a', border: '1px solid rgba(148, 163, 184, 0.35)', borderRadius: 12, color: '#e2e8f0' }}
                    itemStyle={{ color: '#e2e8f0' }}
                    labelStyle={{ color: '#bfdbfe', fontWeight: 700 }}
                    cursor={{ fill: 'rgba(96, 165, 250, 0.08)' }}
                  />
                  <Bar dataKey="events" radius={[10, 10, 4, 4]}>
                    {sourceData.map((datum) => <Cell key={datum.source} fill={datum.fill} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <EmptyAnalyticsState onInject={() => injectEvent.mutate()} isPending={injectEvent.isPending} />
          )}
        </ChartPanel>

        <ChartPanel title="Top users" description="Most active user identifiers" icon={Activity} action={`${formatNumber(topUsers.length)} tracked`}>
          {topUsers.length > 0 ? (
            <div className="space-y-4">
              {topUsers.map((user, index) => {
                const maxEvents = Math.max(...topUsers.map((datum) => datum.events), 1);
                const width = Math.max((user.events / maxEvents) * 100, 8);

                return (
                  <div key={user.user} className="rounded-xl border border-slate-700/60 bg-slate-950/40 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div className="min-w-0">
                        <p className="truncate font-mono text-xs text-slate-200">{user.user}</p>
                        <p className="mt-1 text-xs text-slate-300">Rank #{index + 1}</p>
                      </div>
                      <span className="rounded-full bg-slate-800 px-3 py-1 text-sm font-semibold text-white">{user.events}</span>
                    </div>
                    <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-800">
                      <div className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-cyan-300" style={{ width: `${width}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <EmptyAnalyticsState onInject={() => injectEvent.mutate()} isPending={injectEvent.isPending} />
          )}
        </ChartPanel>
      </div>

      <section className="mt-6 rounded-2xl border border-slate-700/70 bg-slate-900/85 shadow-2xl shadow-black/20">
        <div className="flex flex-col gap-3 border-b border-slate-700/70 p-5 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="section-label">Event table</p>
            <h2 className="mt-1 text-lg font-semibold text-white">Recent event payloads</h2>
          </div>
          <button onClick={() => refetchEvents()} className="btn-secondary border-slate-700 bg-slate-950/60 text-slate-300">Refresh table</button>
        </div>

        {eventsLoading ? (
          <div className="p-8 text-center text-sm text-slate-200">Loading event table...</div>
        ) : recentEvents.length === 0 ? (
          <div className="p-10">
            <EmptyAnalyticsState onInject={() => injectEvent.mutate()} isPending={injectEvent.isPending} />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[880px] text-left text-sm">
              <thead className="bg-slate-950/40 text-xs uppercase tracking-[0.14em] text-slate-300">
                <tr>
                  <th className="px-5 py-4 font-semibold">Event</th>
                  <th className="px-5 py-4 font-semibold">User</th>
                  <th className="px-5 py-4 font-semibold">Source</th>
                  <th className="px-5 py-4 font-semibold">Properties</th>
                  <th className="px-5 py-4 font-semibold">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {recentEvents.map((event) => {
                  const properties = JSON.stringify(event.properties);

                  return (
                    <tr key={event.id} className="transition-colors hover:bg-slate-800/35">
                      <td className="px-5 py-4">
                        <span className="rounded-full bg-blue-400/10 px-3 py-1 font-mono text-xs font-semibold text-blue-200">{event.name}</span>
                      </td>
                      <td className="px-5 py-4 font-mono text-xs text-slate-300">{event.user_id || 'anonymous'}</td>
                      <td className="px-5 py-4">
                        <span className="rounded-full border border-emerald-400/30 bg-emerald-400/10 px-3 py-1 text-xs font-semibold text-emerald-200">{event.source}</span>
                      </td>
                      <td className="max-w-[360px] px-5 py-4 font-mono text-xs text-slate-200">
                        {properties.slice(0, 92)}{properties.length > 92 ? '...' : ''}
                      </td>
                      <td className="whitespace-nowrap px-5 py-4 text-xs text-slate-200">{formatDate(event.timestamp)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="mt-8">
        <div className="mb-4">
          <p className="section-label">Saved workspaces</p>
          <h2 className="mt-1 text-lg font-semibold text-white">Managed dashboards</h2>
        </div>

        {dashboardsLoading ? (
          <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
            {[...Array(3)].map((_, index) => <div key={index} className="h-36 animate-pulse rounded-2xl border border-slate-700/60 bg-slate-900/70" />)}
          </div>
        ) : dashboards.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-700 bg-slate-900/55 p-8 text-center">
            <BarChart3 className="mx-auto mb-3 text-slate-400" size={42} />
            <p className="text-sm text-slate-200">No saved dashboards yet. The live event dashboard above is ready for your demo.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
            {dashboards.map((dashboard: Dashboard) => (
              <div key={dashboard.id} className="rounded-2xl border border-slate-700/70 bg-slate-900/80 p-5 shadow-xl shadow-black/15 transition hover:border-blue-400/40 hover:bg-slate-900">
                <div className="flex items-start justify-between gap-3">
                  <Link href={`/dashboard/dashboards/${dashboard.id}`} className="min-w-0 flex-1">
                    <h3 className="truncate font-semibold text-white transition-colors hover:text-blue-300">{dashboard.name}</h3>
                    {dashboard.description && <p className="mt-1 line-clamp-2 text-sm text-slate-300">{dashboard.description}</p>}
                  </Link>
                  {dashboard.is_public && <span className="rounded-full bg-cyan-400/10 px-2.5 py-1 text-xs font-semibold text-cyan-200">Public</span>}
                </div>
                <div className="mt-5 flex items-center justify-between text-sm text-slate-300">
                  <span>{dashboard.widgets.length} widgets</span>
                  <span>{formatRelativeDate(dashboard.updated_at)}</span>
                </div>
                <div className="mt-5 flex gap-2 border-t border-slate-800 pt-4">
                  <Link href={`/dashboard/dashboards/${dashboard.id}`} className="btn-primary min-h-10 flex-1 text-sm">Open</Link>
                  <button
                    onClick={() => deleteMutation.mutate(dashboard.id)}
                    className="btn-secondary min-h-10 border-slate-700 bg-slate-950/60 px-3 text-slate-300"
                    title="Delete dashboard"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function MetricCard({ icon: Icon, label, value, detail, accent }: { icon: LucideIcon; label: string; value: string; detail: string; accent: string }) {
  return (
    <div className="rounded-2xl border border-slate-700/70 bg-slate-900/80 p-5 shadow-xl shadow-black/15">
      <div className="flex items-center justify-between gap-3">
        <div className={`flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br ${accent} text-white shadow-lg shadow-black/20`}>
          <Icon size={20} />
        </div>
        <span className="rounded-full border border-slate-600 bg-slate-950/70 px-2.5 py-1 text-xs font-semibold text-slate-100">Live</span>
      </div>
      <p className="mt-5 text-sm font-medium text-slate-200">{label}</p>
      <p className="mt-1 text-2xl font-bold text-white">{value}</p>
      <p className="mt-2 truncate text-xs font-medium text-slate-300">{detail}</p>
    </div>
  );
}

function ChartPanel({ title, description, icon: Icon, action, children }: { title: string; description: string; icon: LucideIcon; action: string; children: ReactNode }) {
  return (
    <section className="rounded-2xl border border-slate-700/70 bg-slate-900/85 p-5 shadow-2xl shadow-black/20">
      <div className="mb-5 flex items-start justify-between gap-4">
        <div className="flex min-w-0 items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-blue-400/20 bg-blue-400/10 text-blue-200">
            <Icon size={18} />
          </div>
          <div className="min-w-0">
            <h2 className="truncate text-lg font-semibold text-white">{title}</h2>
            <p className="mt-1 text-sm text-slate-300">{description}</p>
          </div>
        </div>
        <span className="shrink-0 rounded-full border border-slate-600 bg-slate-950/70 px-3 py-1 text-xs font-semibold text-slate-100">{action}</span>
      </div>
      {children}
    </section>
  );
}

function EmptyAnalyticsState({ onInject, isPending }: { onInject: () => void; isPending: boolean }) {
  return (
    <div className="flex min-h-[220px] flex-col items-center justify-center rounded-2xl border border-dashed border-slate-700 bg-slate-950/35 p-8 text-center">
      <Activity className="mb-4 text-slate-400" size={42} />
      <p className="text-sm font-medium text-slate-300">No event data yet</p>
      <p className="mt-1 max-w-sm text-sm text-slate-300">Inject a sample event to populate the charts and table instantly.</p>
      <button onClick={onInject} disabled={isPending} className="btn-primary mt-5 disabled:cursor-not-allowed disabled:opacity-60">
        <Send size={16} />
        {isPending ? 'Injecting...' : 'Inject Event'}
      </button>
    </div>
  );
}
