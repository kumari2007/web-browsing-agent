import React, { useState } from 'react';
import { 
  Compass, 
  Globe, 
  Sliders, 
  Shield, 
  Play, 
  Sparkles, 
  AlertCircle, 
  Layers, 
  Clock, 
  HelpCircle,
  FileSpreadsheet
} from 'lucide-react';
import { api } from '../services/api';
import { NavSection } from '../components/Sidebar';

interface NewTaskViewProps {
  onTaskStarted: (taskId: string) => void;
  onNavigate: (section: NavSection) => void;
}

interface TaskTemplate {
  title: string;
  query: string;
  startUrl: string;
  maxPages: number;
  maxDepth: number;
  schemaFields?: string[];
  description: string;
}

const TEMPLATES: TaskTemplate[] = [
  {
    title: '1. Technical Research & Summarization',
    query: 'Research the architecture, key components, and deployment strategies of Retrieval-Augmented Generation (RAG) systems.',
    startUrl: '',
    maxPages: 3,
    maxDepth: 2,
    description: 'Searches reliable engineering documentation, reads multiple sources, and generates evidence-grounded synthesis.'
  },
  {
    title: '2. Product Spec & Price Comparison',
    query: 'Compare the price, processor, battery life, and display specifications of Apple M3 MacBook Air vs Dell XPS 13.',
    startUrl: '',
    maxPages: 4,
    maxDepth: 2,
    schemaFields: ['price', 'processor', 'battery', 'display', 'ram'],
    description: 'Extracts hardware tables, pricing figures, and side-by-side contrast.'
  },
  {
    title: '3. Structured Data Extraction',
    query: 'Extract official technical specs, release dates, and key features of Python 3.12.',
    startUrl: 'https://docs.python.org/3/whatsnew/3.12.html',
    maxPages: 2,
    maxDepth: 1,
    schemaFields: ['version', 'release_date', 'features'],
    description: 'Navigates directly to starting documentation URL and extracts structured tables and bullet facts.'
  },
  {
    title: '4. Documentation Q&A Navigation',
    query: 'Navigate FastAPI documentation and explain how background tasks and dependency injection work with code examples.',
    startUrl: 'https://fastapi.tiangolo.com/',
    maxPages: 3,
    maxDepth: 2,
    description: 'Follows internal documentation links and retrieves code snippets.'
  },
  {
    title: '5. Multi-Source Evidence Investigation',
    query: 'Investigate recent advances in small language models (SLMs) and cite benchmark evaluation scores.',
    startUrl: '',
    maxPages: 4,
    maxDepth: 3,
    description: 'Crawls multiple destination pages, indexing dense chunks into RAG and mapping claims to evidence.'
  }
];

export const NewTaskView: React.FC<NewTaskViewProps> = ({ onTaskStarted, onNavigate }) => {
  const [query, setQuery] = useState('');
  const [startUrl, setStartUrl] = useState('');
  const [maxPages, setMaxPages] = useState(3);
  const [maxDepth, setMaxDepth] = useState(2);
  const [timeoutSec, setTimeoutSec] = useState(180);
  const [riskPreference, setRiskPreference] = useState('READ_ONLY');
  const [headless, setHeadless] = useState(true);
  const [schemaFieldsText, setSchemaFieldsText] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const applyTemplate = (tpl: TaskTemplate) => {
    setQuery(tpl.query);
    setStartUrl(tpl.startUrl);
    setMaxPages(tpl.maxPages);
    setMaxDepth(tpl.maxDepth);
    setSchemaFieldsText(tpl.schemaFields ? tpl.schemaFields.join(', ') : '');
    setErrorMsg('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) {
      setErrorMsg('Please specify a task or research question.');
      return;
    }

    try {
      setSubmitting(true);
      setErrorMsg('');

      const fields = schemaFieldsText
        ? schemaFieldsText.split(',').map(s => s.trim()).filter(Boolean)
        : undefined;

      const res = await api.createTask({
        query: query.trim(),
        start_url: startUrl.trim() || undefined,
        max_inspect_pages: Number(maxPages),
        max_depth: Number(maxDepth),
        headless: Boolean(headless),
        risk_preference: riskPreference,
        extraction_fields: fields
      });

      onTaskStarted(res.task_id);
      onNavigate('live');
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to dispatch task');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-fadeIn pb-12">
      {/* Templates Selector */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 text-slate-300">
          <Sparkles className="w-4 h-4 text-cyan-400" />
          <h3 className="text-sm font-semibold tracking-tight">Interactive Task Templates</h3>
          <span className="text-xs text-slate-400">— click to load pre-configured parameters</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {TEMPLATES.map((tpl, i) => (
            <button
              key={i}
              type="button"
              onClick={() => applyTemplate(tpl)}
              className="text-left p-3.5 rounded-xl bg-nexus-900 hover:bg-nexus-850 border border-nexus-800 hover:border-cyan-500/40 transition-all group relative overflow-hidden"
            >
              <div className="font-medium text-xs text-white group-hover:text-cyan-300 transition-colors">
                {tpl.title}
              </div>
              <p className="text-[11px] text-slate-400 mt-1 line-clamp-2 leading-relaxed">
                {tpl.description}
              </p>
              <div className="mt-2.5 flex items-center gap-2 text-[10px] text-slate-400 font-mono">
                <span className="px-1.5 py-0.5 rounded bg-nexus-800 border border-nexus-700/60">
                  {tpl.maxPages} pages
                </span>
                <span className="px-1.5 py-0.5 rounded bg-nexus-800 border border-nexus-700/60">
                  Depth {tpl.maxDepth}
                </span>
                {tpl.startUrl && (
                  <span className="px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 truncate max-w-[100px]">
                    Direct URL
                  </span>
                )}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Main Form Card */}
      <form onSubmit={handleSubmit} className="p-6 md:p-8 rounded-2xl bg-nexus-900 border border-nexus-800/90 shadow-xl space-y-6">
        {errorMsg && (
          <div className="p-4 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-3">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Natural Language Task Input */}
        <div className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
            Natural-Language Research Goal or Instruction <span className="text-cyan-400">*</span>
          </label>
          <textarea
            rows={4}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. Compare the specifications, prices, and benchmark scores of RTX 4080 Super vs RX 7900 XTX across authoritative hardware review sites..."
            className="w-full px-4 py-3 rounded-xl bg-nexus-950 border border-nexus-800 text-slate-100 placeholder-slate-400 text-sm focus:outline-none focus:border-cyan-500/60 focus:ring-1 focus:ring-cyan-500/40 transition-all font-sans"
            required
          />
          <p className="text-[11px] text-slate-400">
            Formulate clearly in natural English. The planner decomposes goals into search queries, candidate evaluation, and synthesis steps.
          </p>
        </div>

        {/* Starting URL Input */}
        <div className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center justify-between">
            <span>Starting Destination URL (Optional)</span>
            <span className="text-slate-400 font-normal lowercase font-mono">http:// or https://</span>
          </label>
          <div className="relative">
            <Globe className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="url"
              value={startUrl}
              onChange={(e) => setStartUrl(e.target.value)}
              placeholder="https://example.com/docs or leave blank to auto-discover via web search"
              className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-nexus-950 border border-nexus-800 text-slate-100 placeholder-slate-400 text-xs focus:outline-none focus:border-cyan-500/60 transition-all font-mono"
            />
          </div>
        </div>

        {/* Configuration Parameters Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 pt-2 border-t border-nexus-800/60">
          {/* Max Pages */}
          <div className="space-y-2">
            <label className="block text-xs font-medium text-slate-300 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-cyan-400" />
              <span>Max Pages to Inspect</span>
            </label>
            <input
              type="number"
              min={1}
              max={15}
              value={maxPages}
              onChange={(e) => setMaxPages(Math.max(1, parseInt(e.target.value) || 1))}
              className="w-full px-3 py-2 rounded-xl bg-nexus-950 border border-nexus-800 text-slate-100 text-xs font-mono focus:outline-none focus:border-cyan-500/60"
            />
            <p className="text-[10px] text-slate-400">1 to 15 pages (default 3)</p>
          </div>

          {/* Max Crawl Depth */}
          <div className="space-y-2">
            <label className="block text-xs font-medium text-slate-300 flex items-center gap-1.5">
              <Compass className="w-3.5 h-3.5 text-indigo-400" />
              <span>Max Navigation Depth</span>
            </label>
            <input
              type="number"
              min={1}
              max={5}
              value={maxDepth}
              onChange={(e) => setMaxDepth(Math.max(1, parseInt(e.target.value) || 1))}
              className="w-full px-3 py-2 rounded-xl bg-nexus-950 border border-nexus-800 text-slate-100 text-xs font-mono focus:outline-none focus:border-cyan-500/60"
            />
            <p className="text-[10px] text-slate-400">Multi-hop link discovery limit</p>
          </div>

          {/* Timeout */}
          <div className="space-y-2">
            <label className="block text-xs font-medium text-slate-300 flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-amber-400" />
              <span>Execution Timeout</span>
            </label>
            <input
              type="number"
              min={30}
              max={600}
              step={10}
              value={timeoutSec}
              onChange={(e) => setTimeoutSec(parseInt(e.target.value) || 180)}
              className="w-full px-3 py-2 rounded-xl bg-nexus-950 border border-nexus-800 text-slate-100 text-xs font-mono focus:outline-none focus:border-cyan-500/60"
            />
            <p className="text-[10px] text-slate-400">Seconds before safe termination</p>
          </div>
        </div>

        {/* Structured Schema & Safety Settings */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 pt-2 border-t border-nexus-800/60">
          {/* Structured Extraction Schema */}
          <div className="space-y-2">
            <label className="block text-xs font-medium text-slate-300 flex items-center gap-1.5">
              <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />
              <span>Extraction Schema Fields (Optional)</span>
            </label>
            <input
              type="text"
              value={schemaFieldsText}
              onChange={(e) => setSchemaFieldsText(e.target.value)}
              placeholder="price, rating, release_date, specs"
              className="w-full px-3 py-2 rounded-xl bg-nexus-950 border border-nexus-800 text-slate-100 placeholder-slate-400 text-xs font-mono focus:outline-none focus:border-cyan-500/60"
            />
            <p className="text-[10px] text-slate-400">Comma-separated keys for structured table parser</p>
          </div>

          {/* Risk Preference & Headless Toggle */}
          <div className="space-y-2">
            <label className="block text-xs font-medium text-slate-300 flex items-center gap-1.5">
              <Shield className="w-3.5 h-3.5 text-cyan-400" />
              <span>Safety &amp; Browser Mode</span>
            </label>
            <div className="flex items-center gap-4 pt-1">
              <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-300">
                <input
                  type="checkbox"
                  checked={headless}
                  onChange={(e) => setHeadless(e.target.checked)}
                  className="rounded bg-nexus-950 border-nexus-800 text-cyan-500 focus:ring-cyan-500/30"
                />
                <span>Headless Mode</span>
              </label>

              <select
                value={riskPreference}
                onChange={(e) => setRiskPreference(e.target.value)}
                className="px-2.5 py-1.5 rounded-lg bg-nexus-950 border border-nexus-800 text-xs text-slate-300 focus:outline-none"
              >
                <option value="READ_ONLY">Read-Only Guard (Safe)</option>
                <option value="CONFIRM_CONSEQUENTIAL">Confirm High-Risk Actions</option>
              </select>
            </div>
            <p className="text-[10px] text-slate-400">Restricts form submissions and blocks private loopbacks</p>
          </div>
        </div>

        {/* Submit Button */}
        <div className="pt-4 flex items-center justify-end gap-4 border-t border-nexus-800/60">
          <button
            type="submit"
            disabled={submitting}
            className="px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 via-indigo-600 to-cyan-500 hover:from-cyan-400 hover:to-indigo-500 text-white font-semibold text-sm shadow-lg shadow-cyan-500/25 hover:shadow-cyan-500/40 transition-all flex items-center gap-2.5 active:scale-95 disabled:opacity-50"
          >
            {submitting ? (
              <>
                <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                <span>Formulating Plan &amp; Launching...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-white" />
                <span>Launch Autonomous Agent</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
