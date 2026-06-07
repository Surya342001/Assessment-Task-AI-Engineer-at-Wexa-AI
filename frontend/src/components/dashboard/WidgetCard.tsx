'use client';

import { useQuery } from '@tanstack/react-query';
import { eventsApi } from '@/lib/api';
import type { Widget } from '@/types';
import LineChartWidget from '@/components/charts/LineChartWidget';
import BarChartWidget from '@/components/charts/BarChartWidget';
import PieChartWidget from '@/components/charts/PieChartWidget';
import KPICard from '@/components/charts/KPICard';
import { Loader2 } from 'lucide-react';

interface Props {
  widget: Widget;
  orgId: string;
}

export function WidgetCard({ widget, orgId }: Props) {
  const { query_config } = widget;

  const { data = [], isLoading, isError } = useQuery({
    queryKey: ['widget-data', widget.id, query_config],
    queryFn: () =>
      eventsApi.aggregate(orgId, {
        event_name: query_config.event_name,
        aggregation: query_config.aggregation,
        property_key: query_config.property_key,
        group_by: query_config.group_by,
        interval: query_config.interval || '1h',
        start_time: getStartTime(query_config.time_range),
      }).then((r) => r.data),
    refetchInterval: 60_000,
  });

  return (
    <div className="card h-full min-h-[200px]">
      <div className="px-4 py-3 border-b border-gray-100">
        <h3 className="text-sm font-semibold text-gray-700">{widget.title}</h3>
      </div>
      <div className="p-4">
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <Loader2 className="animate-spin text-sky-500" size={24} />
          </div>
        ) : isError ? (
          <div className="flex items-center justify-center h-32 text-red-400 text-sm">
            Failed to load data
          </div>
        ) : (
          <WidgetContent widget={widget} data={data} />
        )}
      </div>
    </div>
  );
}

function WidgetContent({ widget, data }: { widget: Widget; data: unknown[] }) {
  switch (widget.widget_type) {
    case 'line_chart': return <LineChartWidget data={data as { bucket: string; value: number }[]} />;
    case 'bar_chart': return <BarChartWidget data={data as { bucket: string; value: number }[]} />;
    case 'pie_chart': return <PieChartWidget data={data as { bucket: string; value: number }[]} />;
    case 'kpi_card': return <KPICard data={data as { value: number }[]} title={widget.title} />;
    default: return <p className="text-gray-400 text-sm">Unsupported widget type</p>;
  }
}

function getStartTime(timeRange: string): string {
  const now = new Date();
  const map: Record<string, number> = {
    '1h': 1, '6h': 6, '24h': 24, '7d': 168, '30d': 720, '90d': 2160,
  };
  const hours = map[timeRange] ?? 24;
  return new Date(now.getTime() - hours * 60 * 60 * 1000).toISOString();
}
