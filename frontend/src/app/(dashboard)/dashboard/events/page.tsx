'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '@/store/auth';
import { eventsApi } from '@/lib/api';
import { Activity, Send } from 'lucide-react';
import { formatDate } from '@/lib/utils';
import toast from 'react-hot-toast';
import type { Event } from '@/types';

const eventTemplates = [
  { name: 'page_view', properties: { page: '/dashboard/events', referrer: 'assignment-demo' } },
  { name: 'button_click', properties: { button: 'refresh', component: 'events_stream' } },
  { name: 'report_exported', properties: { format: 'csv', report: 'weekly_summary' } },
  { name: 'alert_checked', properties: { severity: 'medium', status: 'reviewed' } },
];

function createInjectedEvent() {
  const template = eventTemplates[Math.floor(Math.random() * eventTemplates.length)];
  return {
    name: template.name,
    session_id: `frontend-session-${Date.now()}`,
    user_id: 'demo-frontend-user',
    timestamp: new Date().toISOString(),
    properties: {
      ...template.properties,
      injected_from: 'events_page',
      assignment_demo: true,
      value: Math.floor(Math.random() * 900) + 100,
      browser_path: typeof window !== 'undefined' ? window.location.pathname : '/dashboard/events',
    },
  };
}

export default function EventsPage() {
  const { currentOrgId } = useAuthStore();
  const queryClient = useQueryClient();

  const { data: events = [], isLoading, refetch } = useQuery({
    queryKey: ['events', currentOrgId, 'list'],
    queryFn: () =>
      currentOrgId
        ? eventsApi.list(currentOrgId, { limit: 100 }).then((r) => r.data)
        : Promise.resolve([]),
    enabled: !!currentOrgId,
    refetchInterval: 10_000,
  });

  const injectEvent = useMutation({
    mutationFn: async () => {
      if (!currentOrgId) throw new Error('Organization is not ready yet');
      return eventsApi.ingestSingle(currentOrgId, createInjectedEvent());
    },
    onSuccess: async () => {
      toast.success('Event injected into the stream');
      await queryClient.invalidateQueries({ queryKey: ['events', currentOrgId, 'list'] });
      await refetch();
    },
    onError: () => {
      toast.error('Could not inject event');
    },
  });

  const handleInjectEvent = () => injectEvent.mutate();

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Events</h1>
          <p className="text-gray-500 mt-1">Live event stream from your application</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleInjectEvent}
            disabled={!currentOrgId || injectEvent.isPending}
            className="btn-primary text-sm inline-flex items-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed"
          >
            <Send size={16} />
            {injectEvent.isPending ? 'Injecting...' : 'Inject Event'}
          </button>
          <button onClick={() => refetch()} className="btn-secondary text-sm">Refresh</button>
        </div>
      </div>

      <div className="card mb-6 p-5 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="section-label">Frontend event injector</p>
          <h2 className="text-lg font-semibold text-gray-900 mt-1">Send a demo event to the ingestion API</h2>
          <p className="text-sm text-gray-500 mt-1">
            Creates a realistic sample event using the active organization and refreshes the live stream.
          </p>
        </div>
        <code className="rounded-lg bg-gray-50 px-4 py-3 text-xs text-gray-600 md:min-w-[360px]">
          POST /api/orgs/{'{org_id}'}/events/ingest
        </code>
      </div>

      <div className="card">
        <div className="p-4 border-b border-gray-100 flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-sm font-medium text-gray-600">Live Stream</span>
          <span className="text-xs text-gray-400 ml-auto">Auto-refreshes every 10s</span>
        </div>

        {isLoading ? (
          <div className="p-8 text-center">
            <div className="animate-spin w-8 h-8 border-2 border-sky-500 border-t-transparent rounded-full mx-auto" />
          </div>
        ) : events.length === 0 ? (
          <div className="p-16 text-center">
            <Activity className="mx-auto mb-4 text-gray-300" size={48} />
            <p className="text-gray-400">No events yet. Start sending events to your ingestion endpoint.</p>
            <button
              onClick={handleInjectEvent}
              disabled={!currentOrgId || injectEvent.isPending}
              className="btn-primary text-sm inline-flex items-center gap-2 mt-5 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              <Send size={16} />
              {injectEvent.isPending ? 'Injecting...' : 'Inject Sample Event'}
            </button>
            <code className="block mt-4 p-4 bg-gray-50 rounded-lg text-xs text-gray-600 text-left">
              {`POST /api/orgs/{org_id}/events/ingest\n{"name": "page_view", "properties": {"url": "/home"}}`}
            </code>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left px-6 py-3 text-gray-500 font-medium">Event</th>
                  <th className="text-left px-6 py-3 text-gray-500 font-medium">User</th>
                  <th className="text-left px-6 py-3 text-gray-500 font-medium">Source</th>
                  <th className="text-left px-6 py-3 text-gray-500 font-medium">Properties</th>
                  <th className="text-left px-6 py-3 text-gray-500 font-medium">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {events.map((event: Event) => (
                  <tr key={event.id} className="hover:bg-gray-50">
                    <td className="px-6 py-3">
                      <span className="font-mono text-sky-600 bg-sky-50 px-2 py-0.5 rounded text-xs">
                        {event.name}
                      </span>
                    </td>
                    <td className="px-6 py-3 text-gray-500 text-xs">
                      {event.user_id || '—'}
                    </td>
                    <td className="px-6 py-3">
                      <span className="badge bg-gray-100 text-gray-600">{event.source}</span>
                    </td>
                    <td className="px-6 py-3 text-gray-400 text-xs font-mono">
                      {JSON.stringify(event.properties).slice(0, 60)}
                      {JSON.stringify(event.properties).length > 60 && '...'}
                    </td>
                    <td className="px-6 py-3 text-gray-400 text-xs whitespace-nowrap">
                      {formatDate(event.timestamp)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
