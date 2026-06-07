'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { Activity, ArrowUpRight, BarChart3, Bell, CheckCircle2, Database, MousePointerClick, TrendingUp } from 'lucide-react';
import { useAuthStore } from '@/store/auth';
import { alertsApi, dashboardsApi, eventsApi } from '@/lib/api';
import { formatNumber, formatRelativeDate } from '@/lib/utils';
import type { Event } from '@/types';

function formatEventName(name: string) {
  return name
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

function getEventMeaning(event: Event) {
  const properties = event.properties ?? {};

  switch (event.name) {
    case 'page_view':
      return `A page was viewed${typeof properties.page === 'string' ? `: ${properties.page}` : ''}`;
    case 'button_click':
      return `A button was clicked${typeof properties.button === 'string' ? `: ${properties.button}` : ''}`;
    case 'report_exported':
      return `A report was exported${typeof properties.format === 'string' ? ` as ${properties.format.toUpperCase()}` : ''}`;
    case 'alert_checked':
      return `An alert was reviewed${typeof properties.severity === 'string' ? ` (${properties.severity} severity)` : ''}`;
    case 'frontend_injection_test':
      return 'A test event was sent successfully from the frontend';
    default:
      return `${formatEventName(event.name)} was captured by the analytics API`;
  }
}

function getPropertyPreview(event: Event) {
  return Object.entries(event.properties ?? {})
    .slice(0, 3)
    .map(([key, value]) => `${key}: ${String(value)}`);
}

export default function OverviewPage() {
  const { currentOrgId, user } = useAuthStore();

  const { data: recentEvents = [], isLoading: eventsLoading } = useQuery({
    queryKey: ['events', currentOrgId, 'recent'],
    queryFn: () =>
      currentOrgId
        ? eventsApi.list(currentOrgId, { limit: 10 }).then((response) => response.data)
        : Promise.resolve([]),
    enabled: !!currentOrgId,
    refetchInterval: 30_000,
  });

  const { data: dashboards = [] } = useQuery({
    queryKey: ['dashboards', currentOrgId, 'overview'],
    queryFn: () =>
      currentOrgId
        ? dashboardsApi.list(currentOrgId).then((response) => response.data)
        : Promise.resolve([]),
    enabled: !!currentOrgId,
  });

  const { data: alerts = [] } = useQuery({
    queryKey: ['alerts', currentOrgId, 'overview'],
    queryFn: () =>
      currentOrgId
        ? alertsApi.list(currentOrgId).then((response) => response.data)
        : Promise.resolve([]),
    enabled: !!currentOrgId,
  });

  const eventTypes = new Set(recentEvents.map((event) => event.name));
  const latestEvent = recentEvents[0];

  const stats = [
    { label: 'Events received', value: formatNumber(recentEvents.length), detail: 'User actions captured by the app', icon: Activity, tone: 'text-blue-200 bg-blue-500/15' },
    { label: 'Event types', value: formatNumber(eventTypes.size), detail: 'Different actions in the stream', icon: Database, tone: 'text-cyan-200 bg-cyan-500/15' },
    { label: 'Dashboards saved', value: formatNumber(dashboards.length), detail: 'Visual report workspaces', icon: BarChart3, tone: 'text-violet-200 bg-violet-500/15' },
    { label: 'Alerts configured', value: formatNumber(alerts.length), detail: 'Rules watching your data', icon: Bell, tone: 'text-amber-200 bg-amber-500/15' },
  ];

  return (
    <div className="min-h-full p-6 text-slate-100 lg:p-8">
      <header className="mb-8 flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
        <div>
          <p className="section-label">Analytics overview</p>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight text-white">
            Welcome back{user?.full_name ? `, ${user.full_name.split(' ')[0]}` : ''}
          </h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-200">
            This page shows what your app is tracking right now: actions users performed, where those actions came from, and when they arrived.
          </p>
        </div>
        <Link href="/dashboard/events" className="btn-secondary border-slate-700 bg-slate-900 text-slate-100">
          View events
          <ArrowUpRight size={16} />
        </Link>
      </header>

      <section className="mb-8 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {stats.map(({ label, value, detail, icon: Icon, tone }) => (
          <div key={label} className="rounded-2xl border border-slate-700/70 bg-slate-900/85 p-5 shadow-xl shadow-black/15">
            <div className="mb-5 flex items-center justify-between">
              <div className={`rounded-xl p-2.5 ${tone}`}>
                <Icon size={20} />
              </div>
              <span className="rounded-full border border-slate-600 bg-slate-950/70 px-2.5 py-1 text-xs font-semibold text-slate-100">Live</span>
            </div>
            <p className="text-sm font-medium text-slate-200">{label}</p>
            <p className="mt-1 text-3xl font-semibold text-white">{value}</p>
            <p className="mt-2 text-xs font-medium text-slate-300">{detail}</p>
          </div>
        ))}
      </section>

      <section className="mb-8 grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-2xl border border-blue-400/20 bg-blue-400/10 p-5">
          <div className="flex items-start gap-3">
            <div className="rounded-xl bg-blue-400/15 p-2 text-blue-200">
              <CheckCircle2 size={20} />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">What this overview means</h2>
              <p className="mt-2 text-sm leading-6 text-slate-200">
                An event is one tracked action, like a page view, button click, exported report, or alert check. The list below translates each event into a readable activity line.
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-700/70 bg-slate-900/85 p-5">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-emerald-400/10 p-2 text-emerald-200">
              <TrendingUp size={20} />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-200">Latest activity</p>
              <p className="mt-1 text-sm text-slate-300">
                {latestEvent ? `${formatEventName(latestEvent.name)} came in ${formatRelativeDate(latestEvent.timestamp)}` : 'No activity has arrived yet'}
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="overflow-hidden rounded-2xl border border-slate-700/70 bg-slate-900/85 shadow-2xl shadow-black/20">
        <div className="flex flex-col gap-4 border-b border-slate-700/70 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="section-label">Recent activity</p>
            <h2 className="mt-1 text-lg font-semibold text-white">Latest tracked events</h2>
            <p className="mt-1 text-sm text-slate-300">Each row below is one action captured by the analytics API.</p>
          </div>
          <div className="flex items-center gap-2 text-sm font-medium text-slate-100">
            <span className="status-dot" /> Auto refresh enabled
          </div>
        </div>

        {eventsLoading ? (
          <div className="p-10 text-center text-sm text-slate-200">Loading recent events...</div>
        ) : recentEvents.length === 0 ? (
          <div className="p-12 text-center">
            <Activity className="mx-auto mb-3 text-slate-400" size={34} />
            <p className="font-medium text-slate-300">No events yet</p>
            <p className="mt-1 text-sm text-slate-400">Use the Events or Dashboards page to inject a sample event and populate this stream.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-800/80">
            {recentEvents.map((event: Event) => (
              <div key={event.id} className="grid gap-4 px-6 py-5 transition-colors hover:bg-slate-800/35 lg:grid-cols-[1.2fr_0.8fr_130px] lg:items-center">
                <div className="min-w-0 space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-full bg-blue-400/10 px-3 py-1 font-mono text-xs font-semibold text-blue-100">
                      {formatEventName(event.name)}
                    </span>
                    <span className="rounded-full border border-emerald-400/30 bg-emerald-400/10 px-3 py-1 text-xs font-semibold text-emerald-100">
                      {event.source.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-sm font-semibold text-white">{getEventMeaning(event)}</p>
                  <p className="text-xs text-slate-300">
                    User: <span className="font-mono text-slate-100">{event.user_id || 'anonymous'}</span>
                  </p>
                </div>

                <div>
                  <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.12em] text-slate-300">
                    <MousePointerClick size={14} /> Details
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {getPropertyPreview(event).map((property) => (
                      <span key={property} className="max-w-full truncate rounded-lg border border-slate-700 bg-slate-950/60 px-2.5 py-1 text-xs text-slate-200">
                        {property}
                      </span>
                    ))}
                    {Object.keys(event.properties).length === 0 && (
                      <span className="rounded-lg border border-slate-700 bg-slate-950/60 px-2.5 py-1 text-xs text-slate-300">No details</span>
                    )}
                  </div>
                </div>

                <div className="text-left lg:text-right">
                  <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-300">When</p>
                  <p className="mt-1 text-sm font-medium text-slate-100">{formatRelativeDate(event.timestamp)}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
