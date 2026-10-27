import React from 'react';
import { ShieldCheck, Plus, Radio, Server } from 'lucide-react';
import { NavSection } from './Sidebar';

interface TopBarProps {
  currentSection: NavSection;
  onNavigate: (section: NavSection) => void;
  activeTaskId?: string | null;
  serverOnline: boolean;
}

const SECTION_TITLES: Record<NavSection, { title: string; subtitle: string }> = {
  'overview': { title: 'Intelligence Overview', subtitle: 'Global telemetry and research metrics' },
  'new-task': { title: 'New Autonomous Task', subtitle: 'Formulate instructions and configure browser bounds' },
  'live': { title: 'Live Agent Execution', subtitle: 'Real-time DOM navigation, actions, and telemetry' },
  'history': { title: 'Task History & Results', subtitle: 'Audit trajectories, verified citations, and exports' },
  'knowledge': { title: 'Knowledge Base & RAG', subtitle: 'Manage embeddings, uploaded documents, and vector retrieval' },
  'memory': { title: 'Experience Memory', subtitle: 'Recorded locator strategies, failure modes, and guidance' },
  'analytics': { title: 'System Analytics', subtitle: 'Performance charts, duration breakdown, and success trends' },
  'safety': { title: 'Safety & Governance Center', subtitle: 'Action risk boundaries, SSRF filters, and intervention log' },
  'settings': { title: 'System Settings', subtitle: 'LLM providers, model selection, and timeouts' },
};

export const TopBar: React.FC<TopBarProps> = ({
  currentSection,
  onNavigate,
  activeTaskId,
  serverOnline
}) => {
  const info = SECTION_TITLES[currentSection] || { title: 'Dashboard', subtitle: '' };

  return (
    <header className="h-16 bg-nexus-900/60 backdrop-blur-md border-b border-nexus-800/80 sticky top-0 z-20 px-6 flex items-center justify-between">
      {/* Title & Breadcrumb */}
      <div>
        <h1 className="text-lg font-semibold text-white tracking-tight flex items-center gap-2">
          {info.title}
        </h1>
        <p className="text-xs text-slate-400 hidden sm:block">
          {info.subtitle}
        </p>
      </div>

      {/* Action Controls & Indicators */}
      <div className="flex items-center gap-3">
        {/* Active Task Live Pill */}
        {activeTaskId && (
          <button
            onClick={() => onNavigate('live')}
            className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-medium hover:bg-cyan-500/20 transition-all animate-pulse"
          >
            <Radio className="w-3.5 h-3.5 text-cyan-400" />
            <span>Task Active</span>
            <span className="font-mono text-[10px] text-cyan-300">#{activeTaskId.slice(0, 6)}</span>
          </button>
        )}

        {/* Safety Mode Badge */}
        <div className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-nexus-850 border border-nexus-700/60 text-slate-300 text-xs">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span className="font-medium text-slate-300">Read-Only Guard</span>
        </div>

        {/* Server Status Pill */}
        <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-nexus-850 border border-nexus-700/60 text-xs">
          <Server className={`w-3.5 h-3.5 ${serverOnline ? 'text-emerald-400' : 'text-rose-400'}`} />
          <span className="text-[11px] text-slate-400 font-mono">
            {serverOnline ? 'Connected' : 'Offline'}
          </span>
        </div>

        {/* Start Task CTA Button */}
        {currentSection !== 'new-task' && (
          <button
            onClick={() => onNavigate('new-task')}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white text-xs font-semibold shadow-md shadow-cyan-500/15 hover:shadow-cyan-500/30 transition-all active:scale-95"
          >
            <Plus className="w-4 h-4" />
            <span className="hidden sm:inline">Start New Task</span>
          </button>
        )}
      </div>
    </header>
  );
};
