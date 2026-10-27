import React, { useEffect, useState } from 'react';
import { 
  Brain, 
  Search, 
  Trash2, 
  CheckCircle2, 
  XCircle, 
  Sparkles, 
  RefreshCw,
  Lightbulb,
  AlertTriangle
} from 'lucide-react';
import { api } from '../services/api';
import { ExperienceEntry } from '../types';

export const ExperienceMemoryView: React.FC = () => {
  const [entries, setEntries] = useState<ExperienceEntry[]>([]);
  const [filterQuery, setFilterQuery] = useState('');
  const [adviceTopic, setAdviceTopic] = useState('');
  const [adviceResult, setAdviceResult] = useState<{ recommended: any[]; avoid: any[] } | null>(null);
  const [loading, setLoading] = useState(false);
  const [queryingAdvice, setQueryingAdvice] = useState(false);

  const loadExperiences = async () => {
    try {
      setLoading(true);
      const data = await api.listExperiences(100);
      setEntries(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadExperiences();
  }, []);

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this experience entry?')) return;
    try {
      await api.deleteExperience(id);
      loadExperiences();
    } catch (err) {
      console.error(err);
    }
  };

  const handleClearAll = async () => {
    if (!confirm('Clear all stored experience records? This cannot be undone.')) return;
    try {
      await api.clearAllMemory();
      loadExperiences();
      setAdviceResult(null);
    } catch (err) {
      console.error(err);
    }
  };

  const handleGetAdvice = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!adviceTopic.trim()) return;

    try {
      setQueryingAdvice(true);
      const adv = await api.getAdvice(adviceTopic.trim());
      setAdviceResult(adv);
    } catch (err) {
      console.error(err);
    } finally {
      setQueryingAdvice(false);
    }
  };

  const filteredEntries = entries.filter(e => 
    e.domain_or_topic.toLowerCase().includes(filterQuery.toLowerCase()) ||
    e.strategy_type.toLowerCase().includes(filterQuery.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-fadeIn pb-12">
      {/* Experience Guidance & Query Bar */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Memory Guidance Query Form */}
        <div className="lg:col-span-6 p-6 rounded-2xl bg-nexus-900 border border-nexus-800/80 shadow-md space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-slate-300">
              <Lightbulb className="w-5 h-5 text-amber-400" />
              <h3 className="text-sm font-semibold">Query Learned Past Strategies</h3>
            </div>
            <span className="text-[10px] text-slate-400 font-mono">SQLite Strategy Store</span>
          </div>

          <form onSubmit={handleGetAdvice} className="space-y-3">
            <input
              type="text"
              value={adviceTopic}
              onChange={(e) => setAdviceTopic(e.target.value)}
              placeholder="e.g. wikipedia.org, amazon.in, pricing table..."
              className="w-full px-4 py-2.5 rounded-xl bg-nexus-950 border border-nexus-800 text-slate-100 placeholder-slate-400 text-xs focus:outline-none focus:border-cyan-500/60"
            />
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={queryingAdvice || !adviceTopic.trim()}
                className="px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white text-xs font-semibold flex items-center gap-2 transition-all disabled:opacity-50"
              >
                {queryingAdvice ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Brain className="w-3.5 h-3.5" />}
                <span>Fetch Experience Advice</span>
              </button>
            </div>
          </form>

          {/* Advice Output Cards */}
          {adviceResult && (
            <div className="space-y-2 pt-2 border-t border-nexus-800/60 text-xs">
              {adviceResult.recommended.length > 0 && (
                <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 space-y-1">
                  <div className="font-semibold flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Recommended Approaches ({adviceResult.recommended.length})</span>
                  </div>
                  <pre className="text-[11px] font-mono text-emerald-200/90 whitespace-pre-wrap">
                    {JSON.stringify(adviceResult.recommended, null, 2)}
                  </pre>
                </div>
              )}

              {adviceResult.avoid.length > 0 && (
                <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 space-y-1">
                  <div className="font-semibold flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                    <span>Patterns to Avoid ({adviceResult.avoid.length})</span>
                  </div>
                  <pre className="text-[11px] font-mono text-rose-200/90 whitespace-pre-wrap">
                    {JSON.stringify(adviceResult.avoid, null, 2)}
                  </pre>
                </div>
              )}

              {adviceResult.recommended.length === 0 && adviceResult.avoid.length === 0 && (
                <p className="text-slate-400 text-xs italic">
                  No specific past experiences recorded yet for '{adviceTopic}'.
                </p>
              )}
            </div>
          )}
        </div>

        {/* Overview Stats */}
        <div className="lg:col-span-6 p-6 rounded-2xl bg-nexus-900 border border-nexus-800/80 shadow-md flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center gap-2 text-slate-300">
              <Brain className="w-5 h-5 text-indigo-400" />
              <h3 className="text-sm font-semibold">Adaptive Memory Engine</h3>
            </div>
            <p className="text-xs text-slate-300 mt-2 leading-relaxed">
              Stores successful locators, responsive navigation patterns, and failed barrier encounters across tasks.
              The agent planner consults this memory before choosing locators or query structures.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="p-3 rounded-xl bg-nexus-950 border border-nexus-800">
              <span className="text-slate-400">Total Patterns</span>
              <div className="text-xl font-bold text-white font-mono mt-1">{entries.length}</div>
            </div>
            <div className="p-3 rounded-xl bg-nexus-950 border border-nexus-800">
              <span className="text-slate-400">Successful Strategies</span>
              <div className="text-xl font-bold text-emerald-400 font-mono mt-1">
                {entries.filter(e => e.outcome === 'success').length}
              </div>
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <button
              onClick={handleClearAll}
              disabled={entries.length === 0}
              className="px-3.5 py-1.5 rounded-xl bg-rose-500/15 hover:bg-rose-500/25 border border-rose-500/30 text-rose-300 text-xs font-medium transition-all disabled:opacity-40"
            >
              Clear Experience Store
            </button>
          </div>
        </div>
      </div>

      {/* Experience Records Table */}
      <div className="p-5 rounded-2xl bg-nexus-900 border border-nexus-800/80 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h3 className="text-sm font-semibold text-white">Recorded Memory Trajectories</h3>
            <p className="text-xs text-slate-400">Domain-level outcomes guiding future research decisions</p>
          </div>

          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={filterQuery}
                onChange={(e) => setFilterQuery(e.target.value)}
                placeholder="Filter by domain or strategy..."
                className="pl-8 pr-3 py-1.5 rounded-lg bg-nexus-950 border border-nexus-800 text-xs text-slate-200 placeholder-slate-400 focus:outline-none"
              />
            </div>
            <button
              onClick={loadExperiences}
              className="p-1.5 rounded-lg bg-nexus-800 hover:bg-nexus-700 text-slate-300 border border-nexus-700"
              title="Refresh memory records"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {filteredEntries.length === 0 ? (
          <div className="py-12 text-center text-slate-400 border border-dashed border-nexus-800 rounded-xl space-y-2">
            <Brain className="w-10 h-10 mx-auto text-slate-400" />
            <p className="text-sm font-medium">No experience patterns recorded yet</p>
            <p className="text-xs text-slate-400">New patterns are automatically persisted during web navigation</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-nexus-850 text-slate-400 uppercase text-[10px] tracking-wider border-b border-nexus-800">
                <tr>
                  <th className="py-3 px-4">Domain / Target</th>
                  <th className="py-3 px-4">Strategy Type</th>
                  <th className="py-3 px-4">Outcome</th>
                  <th className="py-3 px-4">Times Used</th>
                  <th className="py-3 px-4">Strategy Details</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-nexus-800/60 font-mono">
                {filteredEntries.map((item) => (
                  <tr key={item.id} className="hover:bg-nexus-850/40 transition-colors">
                    <td className="py-3 px-4 max-w-xs truncate font-medium text-slate-200">
                      {item.domain_or_topic}
                    </td>
                    <td className="py-3 px-4 text-slate-400 text-[11px]">
                      {item.strategy_type}
                    </td>
                    <td className="py-3 px-4">
                      {item.outcome === 'success' ? (
                        <span className="inline-flex items-center gap-1 text-emerald-400 text-[11px]">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Success</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-rose-400 text-[11px]">
                          <XCircle className="w-3.5 h-3.5" />
                          <span>Failure</span>
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-cyan-400 font-bold">
                      {item.usage_count}
                    </td>
                    <td className="py-3 px-4 max-w-sm truncate text-slate-400 text-[11px]">
                      {JSON.stringify(item.details)}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => handleDelete(item.id)}
                        className="p-1 rounded text-slate-400 hover:text-rose-400 transition-colors"
                        title="Delete memory entry"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
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
