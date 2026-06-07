'use client';

import { useQuery } from '@tanstack/react-query';
import { useParams } from 'next/navigation';
import { useAuthStore } from '@/store/auth';
import { dashboardsApi, eventsApi } from '@/lib/api';
import { WidgetCard } from '@/components/dashboard/WidgetCard';
import { DashboardHeader } from '@/components/dashboard/DashboardHeader';
import { useWebSocket } from '@/lib/websocket';
import { useCallback } from 'react';
import type { WSMessage } from '@/types';

export default function DashboardDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { currentOrgId } = useAuthStore();

  const { data: dashboard, refetch } = useQuery({
    queryKey: ['dashboard', currentOrgId, id],
    queryFn: () =>
      dashboardsApi.get(currentOrgId!, id).then((r) => r.data),
    enabled: !!(currentOrgId && id),
    refetchInterval: 30_000,
  });

  const handleWSMessage = useCallback((msg: WSMessage) => {
    if (msg.type === 'new_events') refetch();
  }, [refetch]);

  useWebSocket(currentOrgId, handleWSMessage);

  if (!dashboard) {
    return (
      <div className="p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-64" />
          <div className="grid grid-cols-2 gap-4">
            {[...Array(4)].map((_, i) => <div key={i} className="h-48 bg-gray-200 rounded-xl" />)}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <DashboardHeader dashboard={dashboard} orgId={currentOrgId!} onRefresh={refetch} />
      {dashboard.widgets.length === 0 ? (
        <div className="card p-16 text-center mt-6">
          <p className="text-gray-400">No widgets yet. Add your first chart!</p>
        </div>
      ) : (
        <div className="grid grid-cols-12 gap-6 mt-6">
          {dashboard.widgets.map((widget) => (
            <div
              key={widget.id}
              className={`col-span-${widget.position.w || 6}`}
              style={{ gridColumn: `span ${widget.position.w || 6}` }}
            >
              <WidgetCard widget={widget} orgId={currentOrgId!} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
