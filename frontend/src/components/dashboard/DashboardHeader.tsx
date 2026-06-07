'use client';

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { dashboardsApi } from '@/lib/api';
import type { Dashboard } from '@/types';
import { Share2, RefreshCw, Trash2, Link } from 'lucide-react';
import toast from 'react-hot-toast';

interface Props {
  dashboard: Dashboard;
  orgId: string;
  onRefresh: () => void;
}

export function DashboardHeader({ dashboard, orgId, onRefresh }: Props) {
  const qc = useQueryClient();
  const [copied, setCopied] = useState(false);

  const shareMutation = useMutation({
    mutationFn: () => dashboardsApi.share(orgId, dashboard.id).then((r) => r.data),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['dashboard', orgId, dashboard.id] });
      copyToClipboard(data.public_url);
      toast.success('Dashboard shared! Link copied.');
    },
  });

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex items-center justify-between">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{dashboard.name}</h1>
        {dashboard.description && (
          <p className="text-gray-500 mt-1">{dashboard.description}</p>
        )}
        <div className="flex items-center gap-3 mt-2">
          <span className="text-sm text-gray-400">{dashboard.widgets.length} widgets</span>
          {dashboard.refresh_interval && (
            <span className="text-sm text-gray-400">
              Auto-refresh: {dashboard.refresh_interval}s
            </span>
          )}
          {dashboard.is_public && (
            <span className="badge bg-green-100 text-green-700">Public</span>
          )}
        </div>
      </div>
      <div className="flex gap-2">
        <button onClick={onRefresh} className="btn-secondary flex items-center gap-2 text-sm">
          <RefreshCw size={14} />
          Refresh
        </button>
        {dashboard.is_public && dashboard.public_slug ? (
          <button
            onClick={() => copyToClipboard(`${window.location.origin}/public/dashboards/${dashboard.public_slug}`)}
            className="btn-secondary flex items-center gap-2 text-sm"
          >
            <Link size={14} />
            {copied ? 'Copied!' : 'Copy Link'}
          </button>
        ) : (
          <button
            onClick={() => shareMutation.mutate()}
            disabled={shareMutation.isPending}
            className="btn-secondary flex items-center gap-2 text-sm"
          >
            <Share2 size={14} />
            Share
          </button>
        )}
      </div>
    </div>
  );
}
