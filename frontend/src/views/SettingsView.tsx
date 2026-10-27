import React, { useEffect, useState } from 'react';
import { 
  Settings as SettingsIcon, 
  Cpu, 
  Key, 
  Globe, 
  Sliders, 
  CheckCircle2, 
  AlertCircle,
  Eye,
  EyeOff,
  Server
} from 'lucide-react';
import { api } from '../services/api';

export const SettingsView: React.FC = () => {
  const [llmProvider, setLlmProvider] = useState('ollama');
  const [ollamaUrl, setOllamaUrl] = useState('http://localhost:11434');
  const [ollamaModel, setOllamaModel] = useState('llama3.2:3b');
  const [openaiKey, setOpenaiKey] = useState('');
  const [openaiBaseUrl, setOpenaiBaseUrl] = useState('');
  const [openaiModel, setOpenaiModel] = useState('gpt-4o-mini');
  const [headless, setHeadless] = useState(true);
  const [searchProvider, setSearchProvider] = useState('duckduckgo');
  const [readOnly, setReadOnly] = useState(true);

  const [showKey, setShowKey] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const loadConfig = async () => {
    try {
      const cfg = await api.getConfig();
      setLlmProvider(cfg.llm_provider || 'ollama');
      setOllamaUrl(cfg.ollama_base_url || 'http://localhost:11434');
      setOllamaModel(cfg.ollama_model || 'llama3.2:3b');
      setOpenaiModel(cfg.openai_model || 'gpt-4o-mini');
      setHeadless(cfg.browser_headless !== false);
      setSearchProvider(cfg.default_search_provider || 'duckduckgo');
      setReadOnly(cfg.read_only_mode !== false);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadConfig();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      setSaveMsg(null);
      await api.updateConfig({
        llm_provider: llmProvider,
        ollama_base_url: ollamaUrl,
        ollama_model: ollamaModel,
        openai_api_key: openaiKey.trim() || undefined,
        openai_base_url: openaiBaseUrl.trim() || undefined,
        openai_model: openaiModel,
        browser_headless: headless,
        default_search_provider: searchProvider,
        read_only_mode: readOnly
      });
      setSaveMsg({ type: 'success', text: 'Configuration parameters updated successfully.' });
    } catch (err: any) {
      setSaveMsg({ type: 'error', text: err.message || 'Failed to update configuration' });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fadeIn pb-12">
      <form onSubmit={handleSave} className="space-y-6">
        {saveMsg && (
          <div className={`p-4 rounded-xl text-xs flex items-center gap-3 ${
            saveMsg.type === 'success' 
              ? 'bg-emerald-500/15 border border-emerald-500/30 text-emerald-300' 
              : 'bg-rose-500/15 border border-rose-500/30 text-rose-300'
          }`}>
            {saveMsg.type === 'success' ? <CheckCircle2 className="w-4 h-4 shrink-0" /> : <AlertCircle className="w-4 h-4 shrink-0" />}
            <span>{saveMsg.text}</span>
          </div>
        )}

        {/* Section 1: LLM Provider Configuration */}
        <div className="p-6 rounded-2xl bg-nexus-900 border border-nexus-800/80 shadow-md space-y-5">
          <div className="flex items-center gap-2 text-slate-300 border-b border-nexus-800 pb-3">
            <Cpu className="w-5 h-5 text-cyan-400" />
            <div>
              <h3 className="text-sm font-semibold">LLM Inference Provider</h3>
              <p className="text-[11px] text-slate-400">Configure local Ollama, cloud API, or deterministic fallback</p>
            </div>
          </div>

          <div className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300">Active Provider</label>
              <select
                value={llmProvider}
                onChange={(e) => setLlmProvider(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-nexus-950 border border-nexus-800 text-xs text-slate-200 focus:outline-none focus:border-cyan-500/60"
              >
                <option value="ollama">Ollama (Local Open-Source)</option>
                <option value="openai">OpenAI (GPT-4o / GPT-4o-mini)</option>
                <option value="groq">Groq (Llama-3 High-Speed)</option>
                <option value="openrouter">OpenRouter (Multi-Model Gateway)</option>
                <option value="gemini">Google Gemini (OpenAI Endpoint)</option>
                <option value="deterministic">Deterministic Grounded Synthesizer (Offline / No Key)</option>
              </select>
            </div>

            {llmProvider === 'ollama' ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-300">Ollama Base URL</label>
                  <input
                    type="text"
                    value={ollamaUrl}
                    onChange={(e) => setOllamaUrl(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-nexus-950 border border-nexus-800 text-xs font-mono text-slate-200"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-300">Model Name</label>
                  <input
                    type="text"
                    value={ollamaModel}
                    onChange={(e) => setOllamaModel(e.target.value)}
                    placeholder="llama3.2:3b, mistral, qwen2.5"
                    className="w-full px-3 py-2 rounded-xl bg-nexus-950 border border-nexus-800 text-xs font-mono text-slate-200"
                  />
                </div>
              </div>
            ) : llmProvider !== 'deterministic' ? (
              <div className="space-y-4 pt-2">
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-300 flex items-center justify-between">
                    <span>API Key</span>
                    <button
                      type="button"
                      onClick={() => setShowKey(!showKey)}
                      className="text-[11px] text-cyan-400 hover:underline flex items-center gap-1"
                    >
                      {showKey ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                      <span>{showKey ? 'Hide' : 'Show'}</span>
                    </button>
                  </label>
                  <input
                    type={showKey ? 'text' : 'password'}
                    value={openaiKey}
                    onChange={(e) => setOpenaiKey(e.target.value)}
                    placeholder="sk-..."
                    className="w-full px-3 py-2 rounded-xl bg-nexus-950 border border-nexus-800 text-xs font-mono text-slate-200"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-medium text-slate-300">Custom Base URL (Optional)</label>
                    <input
                      type="text"
                      value={openaiBaseUrl}
                      onChange={(e) => setOpenaiBaseUrl(e.target.value)}
                      placeholder="https://api.openai.com/v1"
                      className="w-full px-3 py-2 rounded-xl bg-nexus-950 border border-nexus-800 text-xs font-mono text-slate-200"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs font-medium text-slate-300">Target Model</label>
                    <input
                      type="text"
                      value={openaiModel}
                      onChange={(e) => setOpenaiModel(e.target.value)}
                      placeholder="gpt-4o-mini, llama-3.3-70b-versatile"
                      className="w-full px-3 py-2 rounded-xl bg-nexus-950 border border-nexus-800 text-xs font-mono text-slate-200"
                    />
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-xs text-slate-400 italic">
                Deterministic synthesis uses algorithmic quote alignment and structured claim-source mapping without requiring any local GPU or cloud API keys.
              </p>
            )}
          </div>
        </div>

        {/* Section 2: Browser & Search Settings */}
        <div className="p-6 rounded-2xl bg-nexus-900 border border-nexus-800/80 shadow-md space-y-5">
          <div className="flex items-center gap-2 text-slate-300 border-b border-nexus-800 pb-3">
            <Globe className="w-5 h-5 text-indigo-400" />
            <div>
              <h3 className="text-sm font-semibold">Browser &amp; Exploration Automation</h3>
              <p className="text-[11px] text-slate-400">Playwright execution mode and discovery engines</p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 text-xs">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300">Default Search Provider</label>
              <select
                value={searchProvider}
                onChange={(e) => setSearchProvider(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-nexus-950 border border-nexus-800 text-slate-200"
              >
                <option value="duckduckgo">DuckDuckGo (Privacy-First)</option>
                <option value="bing">Bing Search</option>
                <option value="google">Google Web</option>
                <option value="wikipedia">Wikipedia Direct</option>
              </select>
            </div>

            <div className="space-y-3 pt-4">
              <label className="flex items-center gap-2 cursor-pointer text-slate-300">
                <input
                  type="checkbox"
                  checked={headless}
                  onChange={(e) => setHeadless(e.target.checked)}
                  className="rounded bg-nexus-950 border-nexus-800 text-cyan-500"
                />
                <span className="font-medium">Headless Browser by Default</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer text-slate-300">
                <input
                  type="checkbox"
                  checked={readOnly}
                  onChange={(e) => setReadOnly(e.target.checked)}
                  className="rounded bg-nexus-950 border-nexus-800 text-cyan-500"
                />
                <span className="font-medium">Enforce Read-Only Mode (Recommended)</span>
              </label>
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white text-xs font-semibold shadow-md transition-all disabled:opacity-50"
          >
            {saving ? 'Saving Changes...' : 'Save Configuration'}
          </button>
        </div>
      </form>
    </div>
  );
};
