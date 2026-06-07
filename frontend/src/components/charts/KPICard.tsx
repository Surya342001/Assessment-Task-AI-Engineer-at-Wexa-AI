'use client';

import { formatNumber } from '@/lib/utils';
import { TrendingUp } from 'lucide-react';

interface Props {
  data: { value: number }[];
  title: string;
}

export default function KPICard({ data, title }: Props) {
  const total = data.reduce((sum, d) => sum + (d.value || 0), 0);

  return (
    <div className="flex flex-col items-center justify-center py-4">
      <div className="flex items-center gap-2 text-green-500 mb-2">
        <TrendingUp size={20} />
      </div>
      <p className="text-4xl font-bold text-gray-900">{formatNumber(total)}</p>
      <p className="text-sm text-gray-400 mt-2">{title}</p>
    </div>
  );
}
