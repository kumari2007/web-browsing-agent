import React, { useEffect, useState } from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  Clock, 
  CheckCircle2, 
  XCircle, 
  Layers, 
  FileCheck2, 
  ShieldAlert, 
  RefreshCw,
  PieChart as PieIcon,
  Flame
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid, 
  Legend 
} from 'recharts';
import { api } from '../services/api';
import { MetricsSummary } from '../types';

export const AnalyticsView: React.FC = () => {
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null);
  const [loading, setLoading] = useState(false);

  const loadMetrics = async () => {
    try {
      setLoading(true);
      const data = await api.getMetrics();
      setMetrics(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMetrics();
  }, []);

  const taskTypeData = metrics?.task_types 
    ? Object.entries(metrics.task_types).map(([name, value]) => ({ name, value }))
    : [];

  return (
    <div className="space-y-6 animate-fadeIn pb-12">
      {/* Header Refresh Bar */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-white">System Telemetry &amp; Performance KPIs</h2>
          <p className="text-xs text-slate-400">Measured across all recorded Playwright sessions and RAG queries</p>
        </div>
        <button
          onClick={loadMetrics}
          className="p-2 rounded-xl bg-nexus-900 hover:bg-nexus-850 text-slate-300 border border-nexus-800 flex items-center gap-2 text-xs transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Analytics</span>
        </button>
      </div>

      {/* Top 4 Hero KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-nexus-900 border border-nexus-800 space-y-1">
          <span className="text-xs text-slate-400 font-medium">Task Success Rate</span>
          <div className="text-3xl font-bold text-emerald-400 font-mono">
            {metrics?.success_rate ?? 0}%
          </div>
          <div className="text-[11px] text-slate-400">
            {metrics?.successful_tasks ?? 0} of {metrics?.total_tasks ?? 0} runs completed
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-nexus-900 border border-nexus-800 space-y-1">
          <span className="text-xs text-slate-400 font-medium">Mean Task Duration</span>
          <div className="text-3xl font-bold text-amber-400 font-mono">
            {metrics?.avg_duration_seconds ?? 0}s
          </div>
          <div className="text-[11px] text-slate-400">
            Search, crawl &amp; synthesis lifecycle
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-nexus-900 border border-nexus-800 space-y-1">
          <span className="text-xs text-slate-400 font-medium">Self-Correction Rate</span>
          <div className="text-3xl font-bold text-indigo-400 font-mono">
            {metrics?.recovery_rate ?? 100}%
          </div>
          <div className="text-[11px] text-slate-400">
            {metrics?.total_retries ?? 0} retried action recoveries
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-nexus-900 border border-nexus-800 space-y-1">
          <span className="text-xs text-slate-400 font-medium">Criteria Verification Pass</span>
          <div className="text-3xl font-bold text-cyan-400 font-mono">
            {metrics?.verification_pass_rate ?? 0}%
          </div>
          <div className="text-[11px] text-slate-400">
            Rigorous post-execution auditor
          </div>
        </div>
      </div>

      {/* Secondary Metrics Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-nexus-900/60 border border-nexus-800 text-xs space-y-1">
          <span className="text-slate-400">Total Pages Visited</span>
          <div className="text-xl font-bold text-white font-mono">{metrics?.total_pages_visited ?? 0}</div>
          <div className="text-[10px] text-slate-400">Avg {metrics?.avg_pages_per_task ?? 0} pages/task</div>
        </div>

        <div className="p-4 rounded-xl bg-nexus-900/60 border border-nexus-800 text-xs space-y-1">
          <span className="text-slate-400">Evidence Coverage</span>
          <div className="text-xl font-bold text-cyan-300 font-mono">{metrics?.evidence_coverage_avg ?? 0}%</div>
          <div className="text-[10px] text-slate-400">Citation grounding density</div>
        </div>

        <div className="p-4 rounded-xl bg-nexus-900/60 border border-nexus-800 text-xs space-y-1">
          <span className="text-slate-400">Security Barriers Detected</span>
          <div className="text-xl font-bold text-amber-300 font-mono">{metrics?.captcha_count ?? 0}</div>
          <div className="text-[10px] text-slate-400">CAPTCHAs / Cloudflare</div>
        </div>

        <div className="p-4 rounded-xl bg-nexus-900/60 border border-nexus-800 text-xs space-y-1">
          <span className="text-slate-400">Partial Completions</span>
          <div className="text-xl font-bold text-slate-300 font-mono">{metrics?.partial_tasks ?? 0}</div>
          <div className="text-[10px] text-slate-400">Partial evidence retrieved</div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Trend Area Chart */}
        <div className="lg:col-span-8 p-5 rounded-2xl bg-nexus-900 border border-nexus-800/80 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-white">Execution Trend Timeline</h3>
              <p className="text-xs text-slate-400">Daily task volume, successes, and failures</p>
            </div>
            <span className="text-xs text-slate-400 font-mono">14 Days</span>
          </div>

          <div className="h-72 w-full">
            {metrics?.recent_trends && metrics.recent_trends.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={metrics.recent_trends}>
                  <defs>
                    <linearGradient id="colorSuccess" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10B981" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="#10B981" stopOpacity={0.0}/>
                    </linearGradient>
                    <linearGradient id="colorFailed" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#F43F5E" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="#F43F5E" stopOpacity={0.0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                  <XAxis dataKey="date" stroke="#64748B" fontSize={11} tickLine={false} />
                  <YAxis stroke="#64748B" fontSize={11} tickLine={false} allowDecimals={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0B0F19', borderColor: '#22304F', borderRadius: '12px', fontSize: '12px' }}
                  />
                  <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
                  <Area type="monotone" dataKey="success" stroke="#10B981" strokeWidth={2} fillOpacity={1} fill="url(#colorSuccess)" name="Successful Tasks" />
                  <Area type="monotone" dataKey="failed" stroke="#F43F5E" strokeWidth={2} fillOpacity={1} fill="url(#colorFailed)" name="Failed Tasks" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 text-xs border border-dashed border-nexus-800 rounded-xl space-y-1">
                <TrendingUp className="w-8 h-8 text-slate-400" />
                <p>No historical runs logged yet.</p>
              </div>
            )}
          </div>
        </div>

        {/* Task Type Breakdown Bar Chart */}
        <div className="lg:col-span-4 p-5 rounded-2xl bg-nexus-900 border border-nexus-800/80 space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-white">Task Type Distribution</h3>
            <p className="text-xs text-slate-400">Classified research intent</p>
          </div>

          <div className="h-72 w-full">
            {taskTypeData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={taskTypeData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" horizontal={false} />
                  <XAxis type="number" stroke="#64748B" fontSize={11} tickLine={false} allowDecimals={false} />
                  <YAxis type="category" dataKey="name" stroke="#64748B" fontSize={10} tickLine={false} width={85} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0B0F19', borderColor: '#22304F', borderRadius: '12px', fontSize: '12px' }}
                  />
                  <Bar dataKey="value" fill="#06B6D4" radius={[0, 6, 6, 0]} name="Count" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 text-xs border border-dashed border-nexus-800 rounded-xl space-y-1">
                <BarChart3 className="w-8 h-8 text-slate-400" />
                <p>No task distribution data</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
