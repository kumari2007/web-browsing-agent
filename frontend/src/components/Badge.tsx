import React from 'react';
import { TaskStatus } from '../types';

interface BadgeProps {
  status: TaskStatus | string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<BadgeProps> = ({ status, size = 'md' }) => {
  const getStyle = () => {
    switch (status) {
      case 'COMPLETED':
        return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30';
      case 'RUNNING':
        return 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30 animate-pulse';
      case 'PARTIAL_COMPLETION':
        return 'bg-amber-500/15 text-amber-400 border-amber-500/30';
      case 'FAILED':
        return 'bg-rose-500/15 text-rose-400 border-rose-500/30';
      case 'CANCELLED':
        return 'bg-slate-500/15 text-slate-400 border-slate-500/30';
      case 'PAUSED_FOR_INTERVENTION':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/40 animate-bounce';
      case 'VERIFYING':
        return 'bg-indigo-500/15 text-indigo-400 border-indigo-500/30';
      case 'PENDING':
      default:
        return 'bg-slate-700/30 text-slate-400 border-slate-700';
    }
  };

  const pad = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs font-medium';

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border ${getStyle()} ${pad}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${
        status === 'RUNNING' ? 'bg-cyan-400 animate-ping' :
        status === 'COMPLETED' ? 'bg-emerald-400' :
        status === 'FAILED' ? 'bg-rose-400' :
        status === 'PAUSED_FOR_INTERVENTION' ? 'bg-amber-400' : 'bg-slate-400'
      }`} />
      {status.replace(/_/g, ' ')}
    </span>
  );
};
