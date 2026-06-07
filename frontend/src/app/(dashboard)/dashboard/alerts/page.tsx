'use client';

import { useQuery } from '@tanstack/react-query';
import { useAuthStore } from '@/store/auth';
import { alertsApi } from '@/lib/api';
import { Bell, CheckCircle, VolumeX } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { formatRelativeDate } from '@/lib/utils';
import type { Alert } from '@/types';

const statusColors: Record<string, string> = {
  active: 'badge-active',
  triggered: 'badge-triggered',
  resolved: 'badge-resolved',
  muted: 'badge-muted',
};

export default function AlertsPage() {
  const { currentOrgId } = useAuthStore();
  const qc = useQueryClient();

  const { data: alerts = [], isLoading } = useQuery({
    queryKey: ['alerts', currentOrgId],
    queryFn: () =>
      currentOrgId
        ? alertsApi.list(currentOrgId).then((r) => r.data)
        : Promise.resolve([]),
    enabled: !!currentOrgId,
    refetchInterval: 30_000,
  });

  const muteMutation = useMutation({
    mutationFn: (alertId: string) =>
      alertsApi.mute(currentOrgId!, alertId, 60),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['alerts', currentOrgId] });
      toast.success('Alert muted for 1 hour');
    },
  });

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Alerts</h1>
        <p className="text-gray-500 mt-1">Monitor thresholds and receive notifications</p>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="card p-6 animate-pulse h-24" />
          ))}
        </div>
      ) : alerts.length === 0 ? (
        <div className="card p-16 text-center">
          <Bell className="mx-auto mb-4 text-gray-300" size={48} />
          <p className="text-gray-500">No alerts configured yet.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {alerts.map((alert: Alert) => (
            <div key={alert.id} className="card p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <h3 className="font-semibold text-gray-900">{alert.name}</h3>
                    <span className={statusColors[alert.status]}>{alert.status}</span>
                  </div>
                  {alert.description && (
                    <p className="text-sm text-gray-400 mt-1">{alert.description}</p>
                  )}
                  <p className="text-sm text-gray-500 mt-2">
                    <span className="font-medium">{alert.metric_query.event_name}</span>{' '}
                    {alert.condition} {alert.threshold} over {alert.window_minutes}m window
                  </p>
                  {alert.last_evaluated_at && (
                    <p className="text-xs text-gray-400 mt-1">
                      Last evaluated: {formatRelativeDate(alert.last_evaluated_at)}
                    </p>
                  )}
                </div>
                <div className="flex gap-2">
                  {alert.status !== 'muted' && (
                    <button
                      onClick={() => muteMutation.mutate(alert.id)}
                      className="btn-secondary text-sm flex items-center gap-1"
                    >
                      <VolumeX size={14} />
                      Mute 1h
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
