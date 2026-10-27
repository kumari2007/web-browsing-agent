import React, { useEffect, useState, useRef } from 'react';
import { 
  Radio, 
  Pause, 
  Play, 
  Square, 
  Globe, 
  ExternalLink, 
  Terminal, 
  Camera, 
  Layers, 
  Clock, 
  ShieldAlert, 
  CheckCircle2, 
  AlertTriangle,
  ArrowRight,
  RefreshCw,
  Search,
  FileText
} from 'lucide-react';
import { api } from '../services/api';
import { TaskState } from '../types';
import { StatusBadge } from '../components/Badge';
import { NavSection } from '../components/Sidebar';

interface LiveBrowserViewProps {
  activeTaskId: string | null;
  onNavigate: (section: NavSection) => void;
  onSelectTask: (taskId: string) => void;
}

export const LiveBrowserView: React.FC<LiveBrowserViewProps> = ({
  activeTaskId,
  onNavigate,
  onSelectTask
}) => {
  const [taskState, setTaskState] = useState<TaskState | null>(null);
  const [loading, setLoading] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [resolvingIntervention, setResolvingIntervention] = useState(false);
  const logEndRef = useRef<HTMLDivElement | null>(null);

  // Poll or fetch active task state
  const fetchTask = async (id: string) => {
    try {
      const data = await api.getTask(id);
      setTaskState(data);
      if (data.status === 'PAUSED_FOR_INTERVENTION') {
        setIsPaused(true);
      }
    } catch (err) {
      console.error('Failed to poll task state', err);
    }
  };

  useEffect(() => {
    if (!activeTaskId) return;

    fetchTask(activeTaskId);

    // Setup WebSocket connection
    let ws: WebSocket | null = null;
    try {
      ws = api.connectTaskWebSocket(
        activeTaskId,
        (msg) => {
          fetchTask(activeTaskId);
        },
        (err) => {
          console.warn('WebSocket fallback to polling', err);
        }
      );
    } catch (e) {
      console.warn('WS init error', e);
    }

    // Polling fallback interval
    const interval = setInterval(() => {
      fetchTask(activeTaskId);
    }, 2000);

    return () => {
      clearInterval(interval);
      if (ws) ws.close();
    };
  }, [activeTaskId]);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [taskState?.logs]);

  const handlePause = async () => {
    if (!activeTaskId) return;
    try {
      await api.pauseTask(activeTaskId);
      setIsPaused(true);
      fetchTask(activeTaskId);
    } catch (err) {
      console.error(err);
    }
  };

  const handleResume = async () => {
    if (!activeTaskId) return;
    try {
      await api.resumeTask(activeTaskId);
      setIsPaused(false);
      fetchTask(activeTaskId);
    } catch (err) {
      console.error(err);
    }
  };

  const handleCancel = async () => {
    if (!activeTaskId) return;
    if (!confirm('Are you sure you want to cancel the autonomous agent?')) return;
    try {
      await api.cancelTask(activeTaskId);
      fetchTask(activeTaskId);
    } catch (err) {
      console.error(err);
    }
  };

  const handleResolveCaptcha = async () => {
    try {
      setResolvingIntervention(true);
      await api.resolveIntervention('Operator marked challenge resolved from Live View');
      if (activeTaskId) {
        await api.resumeTask(activeTaskId);
        fetchTask(activeTaskId);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setResolvingIntervention(false);
    }
  };

  if (!activeTaskId || !taskState) {
    return (
      <div className="py-20 flex flex-col items-center justify-center text-slate-400 space-y-4 animate-fadeIn">
        <div className="w-16 h-16 rounded-2xl bg-nexus-900 border border-nexus-800 flex items-center justify-center shadow-lg">
          <Globe className="w-8 h-8 text-cyan-400/60" />
        </div>
        <div className="text-center space-y-1">
          <h3 className="text-base font-semibold text-white">No Live Task Active</h3>
          <p className="text-xs text-slate-400 max-w-sm">
            Launch a new task to view live Playwright browser navigation, real-time action telemetry, and screenshots.
          </p>
        </div>
        <button
          onClick={() => onNavigate('new-task')}
          className="px-4 py-2 rounded-xl bg-cyan-500/15 border border-cyan-500/30 text-cyan-300 text-xs font-semibold hover:bg-cyan-500/25 transition-all"
        >
          Start New Task
        </button>
      </div>
    );
  }

  const latestUrl = taskState.visited_urls && taskState.visited_urls.length > 0
    ? taskState.visited_urls[taskState.visited_urls.length - 1]
    : taskState.start_url || 'Initializing search engine...';

  const hasIntervention = taskState.status === 'PAUSED_FOR_INTERVENTION' || 
    (taskState.interventions && taskState.interventions.some(i => !i.resolved));

  return (
    <div className="space-y-6 animate-fadeIn pb-12">
      {/* Top Status & Controls Header */}
      <div className="p-5 rounded-2xl bg-nexus-900 border border-nexus-800/80 shadow-md space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2.5">
              <span className="font-mono text-xs text-slate-400">Task #{taskState.task_id.slice(0, 8)}</span>
              <StatusBadge status={taskState.status} />
              <span className="text-xs px-2 py-0.5 rounded bg-nexus-800 text-slate-400 font-mono">
                {taskState.task_type}
              </span>
            </div>
            <h2 className="text-base font-semibold text-white truncate max-w-2xl">
              {taskState.query || taskState.original_query}
            </h2>
          </div>

          {/* Action Controls */}
          <div className="flex items-center gap-2 shrink-0">
            {taskState.status === 'RUNNING' && (
              <button
                onClick={handlePause}
                className="px-3.5 py-1.5 rounded-xl bg-nexus-800 hover:bg-nexus-700 text-slate-200 text-xs font-medium border border-nexus-700 flex items-center gap-1.5 transition-all"
              >
                <Pause className="w-3.5 h-3.5" />
                <span>Pause</span>
              </button>
            )}

            {isPaused && taskState.status !== 'COMPLETED' && taskState.status !== 'FAILED' && (
              <button
                onClick={handleResume}
                className="px-3.5 py-1.5 rounded-xl bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 text-xs font-medium border border-cyan-500/40 flex items-center gap-1.5 transition-all"
              >
                <Play className="w-3.5 h-3.5" />
                <span>Resume</span>
              </button>
            )}

            {taskState.status === 'RUNNING' && (
              <button
                onClick={handleCancel}
                className="px-3.5 py-1.5 rounded-xl bg-rose-500/15 hover:bg-rose-500/25 text-rose-300 text-xs font-medium border border-rose-500/30 flex items-center gap-1.5 transition-all"
              >
                <Square className="w-3.5 h-3.5" />
                <span>Cancel</span>
              </button>
            )}

            <button
              onClick={() => {
                onSelectTask(taskState.task_id);
                onNavigate('history');
              }}
              className="px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white text-xs font-semibold shadow-sm transition-all flex items-center gap-1.5"
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Results Explorer</span>
            </button>
          </div>
        </div>

        {/* Browser Location Bar */}
        <div className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-nexus-950 border border-nexus-800 text-xs">
          <Globe className="w-4 h-4 text-cyan-400 shrink-0" />
          <span className="text-slate-400 font-mono text-[11px] truncate flex-1">
            {latestUrl}
          </span>
          {latestUrl.startsWith('http') && (
            <a
              href={latestUrl}
              target="_blank"
              rel="noreferrer"
              className="text-slate-400 hover:text-cyan-400 transition-colors p-1"
              title="Open destination URL in separate tab"
            >
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          )}
        </div>
      </div>

      {/* CAPTCHA / Intervention Banner */}
      {hasIntervention && (
        <div className="p-4 rounded-xl bg-amber-500/15 border border-amber-500/40 text-amber-200 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3 animate-pulse">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />
            <div>
              <div className="font-semibold text-amber-300">
                Security Barrier or CAPTCHA Challenge Detected
              </div>
              <div className="text-[11px] text-amber-200/80">
                Automation paused safely without bot evasion. If running headed, complete the challenge in the browser window, then resume.
              </div>
            </div>
          </div>
          <button
            onClick={handleResolveCaptcha}
            disabled={resolvingIntervention}
            className="px-4 py-2 rounded-lg bg-amber-500 text-nexus-950 font-bold hover:bg-amber-400 text-xs shrink-0 transition-all"
          >
            {resolvingIntervention ? 'Resolving...' : 'Resolve & Resume Task'}
          </button>
        </div>
      )}

      {/* Telemetry Metrics Bar */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <div className="p-3 rounded-xl bg-nexus-900 border border-nexus-800">
          <div className="text-[10px] text-slate-400 uppercase font-mono">Current Step</div>
          <div className="text-lg font-bold text-white font-mono mt-0.5">
            {taskState.metrics?.step_count ?? 0}
          </div>
        </div>

        <div className="p-3 rounded-xl bg-nexus-900 border border-nexus-800">
          <div className="text-[10px] text-slate-400 uppercase font-mono">Pages Visited</div>
          <div className="text-lg font-bold text-cyan-400 font-mono mt-0.5">
            {taskState.visited_urls?.length ?? 0}
          </div>
        </div>

        <div className="p-3 rounded-xl bg-nexus-900 border border-nexus-800">
          <div className="text-[10px] text-slate-400 uppercase font-mono">Evidence Chunks</div>
          <div className="text-lg font-bold text-emerald-400 font-mono mt-0.5">
            {taskState.evidence_items?.length ?? taskState.evidence?.length ?? 0}
          </div>
        </div>

        <div className="p-3 rounded-xl bg-nexus-900 border border-nexus-800">
          <div className="text-[10px] text-slate-400 uppercase font-mono">Retries &amp; Recoveries</div>
          <div className="text-lg font-bold text-indigo-400 font-mono mt-0.5">
            {taskState.metrics?.actions_retried ?? 0}
          </div>
        </div>

        <div className="p-3 rounded-xl bg-nexus-900 border border-nexus-800">
          <div className="text-[10px] text-slate-400 uppercase font-mono">Duration</div>
          <div className="text-lg font-bold text-amber-400 font-mono mt-0.5">
            {taskState.metrics?.total_duration_seconds ? `${taskState.metrics.total_duration_seconds}s` : 'Active'}
          </div>
        </div>
      </div>

      {/* Main Split: Browser Viewport & Terminal Log */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Real Browser Screenshot Viewport */}
        <div className="lg:col-span-7 space-y-3">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="flex items-center gap-1.5 font-medium text-slate-300">
              <Camera className="w-3.5 h-3.5 text-cyan-400" />
              <span>Real Playwright Browser Viewport</span>
            </span>
            <span className="text-[10px] font-mono text-slate-400">
              {taskState.screenshot_path ? 'Live Screenshot Captured' : 'Awaiting Viewport Render'}
            </span>
          </div>

          <div className="aspect-video w-full rounded-2xl bg-nexus-950 border border-nexus-800 overflow-hidden relative shadow-inner flex items-center justify-center group">
            {taskState.screenshot_path ? (
              <img
                src={`/api/screenshots/${taskState.screenshot_path}`}
                alt="Browser Viewport"
                className="w-full h-full object-contain"
                onError={(e) => {
                  (e.target as HTMLElement).style.display = 'none';
                }}
              />
            ) : (
              <div className="flex flex-col items-center justify-center text-slate-400 space-y-2">
                <Globe className="w-12 h-12 text-slate-400 animate-pulse" />
                <p className="text-xs font-mono text-slate-400">Browser active in headless session</p>
                <p className="text-[10px] text-slate-400">Diagnostic screenshots save on key step navigations</p>
              </div>
            )}

            {/* Live Indicator Overlay */}
            <div className="absolute top-3 left-3 px-2 py-1 rounded bg-nexus-950/80 backdrop-blur-md border border-nexus-800 text-[10px] font-mono flex items-center gap-1.5 text-slate-300">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
              <span>{taskState.status === 'RUNNING' ? 'AGENT ACTIVE' : taskState.status}</span>
            </div>
          </div>
        </div>

        {/* Live Terminal & Event Timeline */}
        <div className="lg:col-span-5 space-y-3">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="flex items-center gap-1.5 font-medium text-slate-300">
              <Terminal className="w-3.5 h-3.5 text-indigo-400" />
              <span>Agent Event Stream</span>
            </span>
            <span className="font-mono text-[10px] text-slate-400">{taskState.logs?.length ?? 0} events</span>
          </div>

          <div className="h-[380px] rounded-2xl bg-nexus-950 border border-nexus-800 p-4 font-mono text-xs overflow-y-auto space-y-1.5 scrollbar-thin scrollbar-thumb-nexus-800">
            {taskState.logs && taskState.logs.length > 0 ? (
              taskState.logs.map((log, idx) => {
                const isError = log.includes('error') || log.includes('failed') || log.includes('Failed');
                const isSuccess = log.includes('success') || log.includes('completed') || log.includes('Verified');
                const isSelfCorrect = log.includes('Self-correction') || log.includes('recovery');
                return (
                  <div
                    key={idx}
                    className={`leading-relaxed text-[11px] ${
                      isError ? 'text-rose-400' :
                      isSuccess ? 'text-emerald-400' :
                      isSelfCorrect ? 'text-indigo-300 font-semibold' :
                      'text-slate-300'
                    }`}
                  >
                    {log}
                  </div>
                );
              })
            ) : (
              <div className="text-slate-400 text-xs">Waiting for agent events...</div>
            )}
            <div ref={logEndRef} />
          </div>
        </div>
      </div>
    </div>
  );
};
