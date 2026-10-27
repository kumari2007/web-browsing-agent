import React, { useEffect, useState } from 'react';
import { 
  FileText, 
  Table, 
  Layers, 
  Terminal, 
  CheckSquare, 
  Download, 
  ExternalLink, 
  Clock, 
  AlertCircle,
  FileCheck2,
  Calendar,
  Search,
  Sparkles,
  ArrowRight
} from 'lucide-react';
import { api } from '../services/api';
import { TaskState, VerificationReport, ExtractedEvidence } from '../types';
import { StatusBadge } from '../components/Badge';

interface TaskHistoryViewProps {
  selectedTaskId: string | null;
  onSelectTask: (taskId: string) => void;
}

type TabType = 'answer' | 'extracted' | 'evidence' | 'logs' | 'verification';

export const TaskHistoryView: React.FC<TaskHistoryViewProps> = ({
  selectedTaskId,
  onSelectTask
}) => {
  const [tasks, setTasks] = useState<TaskState[]>([]);
  const [currentTask, setCurrentTask] = useState<TaskState | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('answer');
  const [loading, setLoading] = useState(false);
  const [searchFilter, setSearchFilter] = useState('');

  const loadHistory = async () => {
    try {
      setLoading(true);
      const list = await api.listTasks(50);
      setTasks(list);
      if (selectedTaskId) {
        const found = list.find(t => t.task_id === selectedTaskId);
        if (found) {
          const detailed = await api.getTask(selectedTaskId);
          setCurrentTask(detailed);
        } else if (list.length > 0) {
          const detailed = await api.getTask(list[0].task_id);
          setCurrentTask(detailed);
        }
      } else if (list.length > 0) {
        const detailed = await api.getTask(list[0].task_id);
        setCurrentTask(detailed);
      }
    } catch (err) {
      console.error('Failed to load history', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, [selectedTaskId]);

  const handleSelect = async (tId: string) => {
    onSelectTask(tId);
    try {
      const detailed = await api.getTask(tId);
      setCurrentTask(detailed);
    } catch (e) {
      console.error(e);
    }
  };

  const filteredTasks = tasks.filter(t => 
    (t.query || t.original_query || '').toLowerCase().includes(searchFilter.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-fadeIn pb-12">
      {/* Search & Master-Detail Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Task History List */}
        <div className="lg:col-span-4 space-y-3">
          <div className="flex items-center justify-between text-xs text-slate-300">
            <span className="font-semibold uppercase tracking-wider">Historical Runs</span>
            <span className="text-slate-400 font-mono text-[11px]">{tasks.length} tasks</span>
          </div>

          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              placeholder="Search previous tasks..."
              className="w-full pl-9 pr-3 py-2 rounded-xl bg-nexus-900 border border-nexus-800 text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:border-cyan-500/60"
            />
          </div>

          <div className="max-h-[640px] overflow-y-auto space-y-2 pr-1 scrollbar-thin scrollbar-thumb-nexus-800">
            {filteredTasks.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-400 border border-dashed border-nexus-800 rounded-xl">
                No matching tasks found
              </div>
            ) : (
              filteredTasks.map((t) => {
                const isSelected = currentTask?.task_id === t.task_id;
                return (
                  <button
                    key={t.task_id}
                    onClick={() => handleSelect(t.task_id)}
                    className={`w-full text-left p-3.5 rounded-xl border transition-all text-xs space-y-2 ${
                      isSelected
                        ? 'bg-nexus-850 border-cyan-500/50 shadow-sm shadow-cyan-500/10'
                        : 'bg-nexus-900 hover:bg-nexus-850/70 border-nexus-800/80 text-slate-300'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <StatusBadge status={t.status} size="sm" />
                      <span className="text-[10px] font-mono text-slate-400">
                        {t.created_at ? new Date(t.created_at * 1000).toLocaleDateString() : ''}
                      </span>
                    </div>

                    <div className="font-medium text-slate-200 line-clamp-2 leading-relaxed">
                      {t.query || t.original_query}
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1 border-t border-nexus-800/50 font-mono">
                      <span>{t.task_type}</span>
                      <span>{t.metrics?.pages_visited ?? t.visited_urls?.length ?? 0} pages</span>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Right Column: Detailed Results & Evidence Explorer */}
        <div className="lg:col-span-8">
          {currentTask ? (
            <div className="space-y-4">
              {/* Task Header & Exports */}
              <div className="p-5 rounded-2xl bg-nexus-900 border border-nexus-800/80 space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs text-slate-400">ID: {currentTask.task_id.slice(0, 8)}</span>
                      <StatusBadge status={currentTask.status} size="sm" />
                      <span className="text-[11px] px-2 py-0.5 rounded bg-nexus-800 text-slate-400 font-mono">
                        {currentTask.task_type}
                      </span>
                    </div>
                    <h2 className="text-base font-semibold text-white">
                      {currentTask.query || currentTask.original_query}
                    </h2>
                  </div>

                  {/* Export Options */}
                  <div className="flex items-center gap-2">
                    <a
                      href={`/api/tasks/${currentTask.task_id}/export/json`}
                      download
                      className="px-3 py-1.5 rounded-lg bg-nexus-800 hover:bg-nexus-700 text-slate-200 text-xs font-medium border border-nexus-700 flex items-center gap-1.5 transition-colors"
                    >
                      <Download className="w-3.5 h-3.5 text-cyan-400" />
                      <span>JSON</span>
                    </a>
                    <a
                      href={`/api/tasks/${currentTask.task_id}/export/csv`}
                      download
                      className="px-3 py-1.5 rounded-lg bg-nexus-800 hover:bg-nexus-700 text-slate-200 text-xs font-medium border border-nexus-700 flex items-center gap-1.5 transition-colors"
                    >
                      <Download className="w-3.5 h-3.5 text-emerald-400" />
                      <span>CSV</span>
                    </a>
                  </div>
                </div>

                {/* Sub-tabs Navigation */}
                <div className="flex items-center gap-1 border-t border-nexus-800 pt-3 overflow-x-auto text-xs">
                  {[
                    { id: 'answer' as TabType, label: 'Answer & Synthesis', icon: FileText },
                    { id: 'extracted' as TabType, label: `Extracted Data (${currentTask.extracted_records?.length ?? 0})`, icon: Table },
                    { id: 'evidence' as TabType, label: `Evidence (${currentTask.evidence?.length ?? currentTask.evidence_items?.length ?? 0})`, icon: Layers },
                    { id: 'verification' as TabType, label: 'Verification Report', icon: CheckSquare },
                    { id: 'logs' as TabType, label: `Logs (${currentTask.logs?.length ?? 0})`, icon: Terminal },
                  ].map((tb) => {
                    const Icon = tb.icon;
                    const isTabActive = activeTab === tb.id;
                    return (
                      <button
                        key={tb.id}
                        onClick={() => setActiveTab(tb.id)}
                        className={`px-3 py-2 rounded-xl font-medium transition-all flex items-center gap-2 shrink-0 ${
                          isTabActive
                            ? 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/30'
                            : 'text-slate-400 hover:text-slate-200 hover:bg-nexus-850'
                        }`}
                      >
                        <Icon className="w-3.5 h-3.5" />
                        <span>{tb.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Tab 1: Grounded Answer & Citations */}
              {activeTab === 'answer' && (
                <div className="p-6 rounded-2xl bg-nexus-900 border border-nexus-800/80 space-y-4">
                  <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-cyan-400">
                    <Sparkles className="w-4 h-4" />
                    <span>Evidence-Grounded Research Answer</span>
                  </div>

                  {currentTask.final_answer ? (
                    <div className="prose prose-invert prose-cyan max-w-none text-sm leading-relaxed text-slate-200 space-y-3 whitespace-pre-wrap font-sans">
                      {currentTask.final_answer}
                    </div>
                  ) : (
                    <div className="py-8 text-center text-xs text-slate-400 space-y-2">
                      <Clock className="w-8 h-8 mx-auto text-slate-400 animate-pulse" />
                      <p>Final answer synthesis not ready or task ended before completion.</p>
                    </div>
                  )}

                  {/* Visited Sources Footnote */}
                  {currentTask.visited_urls && currentTask.visited_urls.length > 0 && (
                    <div className="mt-6 pt-4 border-t border-nexus-800 space-y-2">
                      <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                        Visited Primary Source URLs
                      </h4>
                      <ul className="space-y-1 text-xs">
                        {currentTask.visited_urls.map((url, i) => (
                          <li key={i} className="flex items-center gap-2 text-slate-400 hover:text-cyan-300">
                            <span className="text-cyan-500 font-mono">[{i + 1}]</span>
                            <a href={url} target="_blank" rel="noreferrer" className="truncate hover:underline flex items-center gap-1 font-mono text-[11px]">
                              <span>{url}</span>
                              <ExternalLink className="w-3 h-3 shrink-0" />
                            </a>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Tab 2: Extracted Data Table */}
              {activeTab === 'extracted' && (
                <div className="p-5 rounded-2xl bg-nexus-900 border border-nexus-800/80 space-y-4">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold uppercase tracking-wider text-slate-300">
                      Structured Fact Table
                    </span>
                    <span className="text-slate-400 font-mono text-[11px]">
                      {currentTask.extracted_records?.length ?? 0} rows extracted
                    </span>
                  </div>

                  {currentTask.extracted_records && currentTask.extracted_records.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-nexus-850 text-slate-400 uppercase text-[10px] tracking-wider border-b border-nexus-800">
                          <tr>
                            {Object.keys(currentTask.extracted_records[0]).map((col) => (
                              <th key={col} className="py-3 px-4 font-mono">{col}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-nexus-800/60 font-mono">
                          {currentTask.extracted_records.map((row, idx) => (
                            <tr key={idx} className="hover:bg-nexus-850/40">
                              {Object.entries(row).map(([k, val], cIdx) => (
                                <td key={cIdx} className="py-3 px-4 max-w-xs truncate text-slate-300">
                                  {typeof val === 'object' ? JSON.stringify(val) : String(val)}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="py-12 text-center text-xs text-slate-400 border border-dashed border-nexus-800 rounded-xl space-y-1">
                      <Table className="w-8 h-8 mx-auto text-slate-400" />
                      <p>No tabular structured records found on visited pages.</p>
                      <p className="text-[11px] text-slate-400">Regular article text was preserved in the Evidence tab.</p>
                    </div>
                  )}
                </div>
              )}

              {/* Tab 3: Evidence Cards */}
              {activeTab === 'evidence' && (
                <div className="space-y-3">
                  {(currentTask.evidence || currentTask.evidence_items || []).map((ev, i) => (
                    <div key={i} className="p-4 rounded-xl bg-nexus-900 border border-nexus-800 space-y-2">
                      <div className="flex items-center justify-between text-xs">
                        <a 
                          href={ev.url} 
                          target="_blank" 
                          rel="noreferrer" 
                          className="font-semibold text-cyan-300 hover:underline flex items-center gap-1.5"
                        >
                          <span>{ev.title || ev.url}</span>
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                        <span className="px-2 py-0.5 rounded bg-nexus-800 font-mono text-[10px] text-slate-400">
                          Relevance: {Math.round(ev.relevance_score * 100)}%
                        </span>
                      </div>
                      <p className="text-xs text-slate-300 leading-relaxed font-sans line-clamp-4 bg-nexus-950 p-3 rounded-lg border border-nexus-800/60">
                        {ev.content}
                      </p>
                      <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono">
                        <span className="truncate max-w-sm">{ev.url}</span>
                        <span>{ev.observed_at}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Tab 4: Verification Report */}
              {activeTab === 'verification' && (
                <div className="p-5 rounded-2xl bg-nexus-900 border border-nexus-800/80 space-y-5">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-semibold text-white">Criteria Verification Auditor</h3>
                      <p className="text-xs text-slate-400">Audits completion status, coverage, and limitations</p>
                    </div>
                    {currentTask.verification_report && (
                      <span className={`px-2.5 py-1 rounded-full text-xs font-bold font-mono ${
                        currentTask.verification_report.is_successful 
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                          : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                      }`}>
                        Verdict: {currentTask.verification_report.status_verdict}
                      </span>
                    )}
                  </div>

                  {currentTask.verification_report ? (
                    <div className="space-y-4 text-xs">
                      {/* Metric scores */}
                      <div className="grid grid-cols-2 gap-4">
                        <div className="p-3 rounded-xl bg-nexus-950 border border-nexus-800">
                          <span className="text-slate-400 text-[11px]">Confidence Score</span>
                          <div className="text-lg font-bold text-cyan-400 font-mono mt-0.5">
                            {Math.round(currentTask.verification_report.confidence_score * 100)}%
                          </div>
                        </div>
                        <div className="p-3 rounded-xl bg-nexus-950 border border-nexus-800">
                          <span className="text-slate-400 text-[11px]">Evidence Coverage</span>
                          <div className="text-lg font-bold text-emerald-400 font-mono mt-0.5">
                            {Math.round(currentTask.verification_report.evidence_coverage * 100)}%
                          </div>
                        </div>
                      </div>

                      {/* Verified Reasons Checklist */}
                      <div className="space-y-2">
                        <h4 className="font-semibold text-slate-300">Satisfied Criteria</h4>
                        <div className="space-y-1.5">
                          {currentTask.verification_report.reasons.map((r, idx) => (
                            <div key={idx} className="flex items-start gap-2 text-slate-300">
                              <CheckSquare className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                              <span>{r}</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Missing or Limitations */}
                      {currentTask.verification_report.limitations && currentTask.verification_report.limitations.length > 0 && (
                        <div className="space-y-2 pt-3 border-t border-nexus-800">
                          <h4 className="font-semibold text-amber-300">Identified Limitations</h4>
                          <div className="space-y-1.5">
                            {currentTask.verification_report.limitations.map((lim, idx) => (
                              <div key={idx} className="flex items-start gap-2 text-slate-400">
                                <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                                <span>{lim}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="py-8 text-center text-xs text-slate-400">
                      Verification auditor has not produced a report for this task yet.
                    </div>
                  )}
                </div>
              )}

              {/* Tab 5: Execution Log */}
              {activeTab === 'logs' && (
                <div className="p-5 rounded-2xl bg-nexus-950 border border-nexus-800 font-mono text-xs max-h-[500px] overflow-y-auto space-y-1.5 scrollbar-thin scrollbar-thumb-nexus-800">
                  {currentTask.logs && currentTask.logs.length > 0 ? (
                    currentTask.logs.map((log, i) => (
                      <div key={i} className="text-slate-300 leading-relaxed text-[11px]">
                        {log}
                      </div>
                    ))
                  ) : (
                    <div className="text-slate-400">No logs recorded.</div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="p-12 text-center text-slate-400 border border-dashed border-nexus-800 rounded-2xl">
              Select a task from the historical list to inspect results and evidence.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
