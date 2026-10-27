import React, { useEffect, useState } from 'react';
import { 
  CheckCircle2, 
  XCircle, 
  Clock, 
  ShieldCheck, 
  TrendingUp, 
  ExternalLink, 
  ArrowUpRight, 
  Sparkles,
  Layers,
  Search,
  FileCheck2,
  RefreshCw
} from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from 'recharts';
import { api } from '../services/api';
import { MetricsSummary, TaskState } from '../types';
import { StatusBadge } from '../components/Badge';
import { NavSection } from '../components/Sidebar';

interface OverviewViewProps {
  onNavigate: (section: NavSection) => void;
  onSelectTask: (taskId: string) => void;
}

export const OverviewView: React.FC<OverviewViewProps> = ({ onNavigate, onSelectTask }) => {
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null);
  const [recentTasks, setRecentTasks] = useState<TaskState[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      setLoading(true);
      const [m, t] = await Promise.all([
        api.getMetrics(),
        api.listTasks(8)
      ]);
      setMetrics(m);
      setRecentTasks(t);
    } catch (err) {
      console.error('Failed to load overview data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Welcome Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-nexus-900 via-nexus-850 to-nexus-900 border border-nexus-700/60 p-6 md:p-8">
        <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="max-w-xl space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 text-xs font-medium">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
              <span>NEXUS Web Intelligence Engine Active</span>
            </div>
            <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-white">
              Autonomous Research &amp; Deep Web Navigation
            </h2>
            <p className="text-sm text-slate-300 leading-relaxed">
              Accepts natural-language research goals, parses DOM structures, retrieves knowledge via RAG, self-corrects failures, and outputs verified citations.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={() => onNavigate('new-task')}
              className="px-5 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white font-semibold text-sm shadow-lg shadow-cyan-500/20 hover:shadow-cyan-500/40 transition-all flex items-center gap-2"
            >
              <span>Start New Task</span>
              <ArrowUpRight className="w-4 h-4" />
            </button>
            <button
              onClick={loadData}
              className="p-3 rounded-xl bg-nexus-800 hover:bg-nexus-700 text-slate-300 border border-nexus-700/60 transition-colors"
              title="Refresh overview metrics"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {/* Total Tasks */}
        <div className="p-4 rounded-xl bg-nexus-900 border border-nexus-800/80 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium">Total Tasks</span>
            <Layers className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            {metrics?.total_tasks ?? 0}
          </div>
          <div className="text-[11px] text-slate-400">
            Executed historically
          </div>
        </div>

        {/* Success Rate */}
        <div className="p-4 rounded-xl bg-nexus-900 border border-nexus-800/80 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium">Success Rate</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 font-mono">
            {metrics?.success_rate ?? 0}%
          </div>
          <div className="text-[11px] text-slate-400">
            {metrics?.successful_tasks ?? 0} completed
          </div>
        </div>

        {/* Failed Tasks */}
        <div className="p-4 rounded-xl bg-nexus-900 border border-nexus-800/80 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium">Failed Tasks</span>
            <XCircle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-bold text-rose-400 font-mono">
            {metrics?.failed_tasks ?? 0}
          </div>
          <div className="text-[11px] text-slate-400">
            Rate: {metrics?.failure_rate ?? 0}%
          </div>
        </div>

        {/* Avg Duration */}
        <div className="p-4 rounded-xl bg-nexus-900 border border-nexus-800/80 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium">Avg Duration</span>
            <Clock className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            {metrics?.avg_duration_seconds ?? 0}s
          </div>
          <div className="text-[11px] text-slate-400">
            Per completed task
          </div>
        </div>

        {/* Self-Correction Recovery */}
        <div className="p-4 rounded-xl bg-nexus-900 border border-nexus-800/80 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium">Recovery Rate</span>
            <TrendingUp className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold text-indigo-400 font-mono">
            {metrics?.recovery_rate ?? 100}%
          </div>
          <div className="text-[11px] text-slate-400">
            {metrics?.total_retries ?? 0} retries handled
          </div>
        </div>

        {/* Evidence Coverage */}
        <div className="p-4 rounded-xl bg-nexus-900 border border-nexus-800/80 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium">Evidence Cov.</span>
            <FileCheck2 className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-cyan-300 font-mono">
            {metrics?.evidence_coverage_avg ?? 0}%
          </div>
          <div className="text-[11px] text-slate-400">
            Verified citations
          </div>
        </div>
      </div>

      {/* Charts & Feature Health */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Task Volume Trend Chart */}
        <div className="lg:col-span-2 p-5 rounded-2xl bg-nexus-900 border border-nexus-800/80 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-white">Execution Trends</h3>
              <p className="text-xs text-slate-400">Task volume and average duration over time</p>
            </div>
            <button 
              onClick={() => onNavigate('analytics')}
              className="text-xs text-cyan-400 hover:text-cyan-300 font-medium flex items-center gap-1"
            >
              <span>Full Analytics</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="h-60 w-full">
            {metrics && metrics.recent_trends && metrics.recent_trends.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={metrics.recent_trends}>
                  <defs>
                    <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#06B6D4" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="#06B6D4" stopOpacity={0.0}/>
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="date" stroke="#475569" fontSize={11} tickLine={false} />
                  <YAxis stroke="#475569" fontSize={11} tickLine={false} allowDecimals={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0B0F19', borderColor: '#22304F', borderRadius: '12px', fontSize: '12px' }}
                  />
                  <Area type="monotone" dataKey="total" stroke="#06B6D4" strokeWidth={2} fillOpacity={1} fill="url(#colorTotal)" name="Tasks" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 space-y-2 border border-dashed border-nexus-800 rounded-xl">
                <Search className="w-8 h-8 text-slate-400" />
                <p className="text-xs">No historical execution trends yet</p>
                <p className="text-[11px] text-slate-400">Launch a task to begin tracking daily activity</p>
              </div>
            )}
          </div>
        </div>

        {/* Feature Health Indicator Checklist */}
        <div className="p-5 rounded-2xl bg-nexus-900 border border-nexus-800/80 space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-white">10 Core Capabilities</h3>
            <p className="text-xs text-slate-400">Subsystem operational status</p>
          </div>

          <div className="space-y-2 text-xs">
            {[
              { name: '1. Self-Correction Engine', status: 'Online', desc: 'Bounded locator & nav recovery' },
              { name: '2. Relevance Search Filter', status: 'Online', desc: 'Lexical + BM25 ranking' },
              { name: '3. Deep Website Navigation', status: 'Online', desc: 'Link discovery queue' },
              { name: '4. Evidence-Based Answers', status: 'Online', desc: 'Verified citation provenance' },
              { name: '5. Task Verification', status: 'Online', desc: 'Completion criteria auditor' },
              { name: '6. Experience Memory', status: 'Online', desc: 'SQLite strategy store' },
              { name: '7. CAPTCHA Safe Handling', status: 'Online', desc: 'Barrier pause & alert' },
              { name: '8. Risk-Aware Browsing', status: 'Online', desc: 'Read-only security gate' },
              { name: '9. Structured Extraction', status: 'Online', desc: 'Spec, price & table parser' },
              { name: '10. Performance Monitoring', status: 'Online', desc: 'Durations & telemetry metrics' },
            ].map((f, idx) => (
              <div key={idx} className="flex items-center justify-between p-2 rounded-lg bg-nexus-850/60 border border-nexus-800/60">
                <div className="truncate pr-2">
                  <div className="font-medium text-slate-200">{f.name}</div>
                  <div className="text-[10px] text-slate-400 truncate">{f.desc}</div>
                </div>
                <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] font-mono shrink-0">
                  {f.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Browsing Tasks */}
      <div className="p-5 rounded-2xl bg-nexus-900 border border-nexus-800/80 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-white">Recent Research Tasks</h3>
            <p className="text-xs text-slate-400">Recently executed queries and outcomes</p>
          </div>
          <button 
            onClick={() => onNavigate('history')}
            className="text-xs text-cyan-400 hover:text-cyan-300 font-medium flex items-center gap-1"
          >
            <span>View All History</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {recentTasks.length === 0 ? (
          <div className="py-12 flex flex-col items-center justify-center text-slate-400 space-y-3 border border-dashed border-nexus-800 rounded-xl">
            <Layers className="w-10 h-10 text-slate-400" />
            <p className="text-sm font-medium text-slate-400">No tasks executed yet</p>
            <button
              onClick={() => onNavigate('new-task')}
              className="px-4 py-2 rounded-xl bg-cyan-500/15 border border-cyan-500/30 text-cyan-300 text-xs font-semibold hover:bg-cyan-500/25 transition-all"
            >
              Start First Autonomous Task
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-nexus-850 text-slate-400 uppercase text-[10px] tracking-wider border-b border-nexus-800">
                <tr>
                  <th className="py-3 px-4">Task Goal</th>
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Pages</th>
                  <th className="py-3 px-4">Duration</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-nexus-800/60">
                {recentTasks.map((t) => (
                  <tr 
                    key={t.task_id} 
                    className="hover:bg-nexus-850/50 transition-colors cursor-pointer group"
                    onClick={() => {
                      onSelectTask(t.task_id);
                      onNavigate('history');
                    }}
                  >
                    <td className="py-3 px-4 max-w-xs truncate font-medium text-slate-200 group-hover:text-cyan-300">
                      {t.query || t.original_query}
                    </td>
                    <td className="py-3 px-4 text-slate-400 font-mono text-[11px]">
                      {t.task_type}
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={t.status} size="sm" />
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-300">
                      {t.metrics?.pages_visited ?? t.visited_urls?.length ?? 0}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-400">
                      {t.metrics?.total_duration_seconds ? `${t.metrics.total_duration_seconds}s` : '—'}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <span className="inline-flex items-center gap-1 text-cyan-400 font-medium group-hover:underline">
                        <span>Details</span>
                        <ExternalLink className="w-3 h-3" />
                      </span>
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
};
