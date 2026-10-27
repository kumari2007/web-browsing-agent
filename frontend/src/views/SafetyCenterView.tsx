import React, { useEffect, useState } from 'react';
import { 
  ShieldAlert, 
  ShieldCheck, 
  AlertTriangle, 
  Lock, 
  CheckCircle2, 
  ExternalLink, 
  RefreshCw,
  Ban,
  Filter,
  EyeOff,
  UserCheck
} from 'lucide-react';
import { api } from '../services/api';
import { SafetyStatus, InterventionRequest } from '../types';

export const SafetyCenterView: React.FC = () => {
  const [safety, setSafety] = useState<SafetyStatus | null>(null);
  const [interventions, setInterventions] = useState<{
    current_active: InterventionRequest | null;
    total_requests: number;
    history: InterventionRequest[];
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [resolving, setResolving] = useState(false);
  const [resolutionNotes, setResolutionNotes] = useState('');

  const loadSafety = async () => {
    try {
      setLoading(true);
      const [s, iv] = await Promise.all([
        api.getSafetyStatus(),
        api.getInterventions()
      ]);
      setSafety(s);
      setInterventions(iv);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSafety();
  }, []);

  const handleResolve = async () => {
    try {
      setResolving(true);
      await api.resolveIntervention(resolutionNotes || 'Approved via Safety Center dashboard');
      setResolutionNotes('');
      loadSafety();
    } catch (err) {
      console.error(err);
    } finally {
      setResolving(false);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn pb-12">
      {/* Pending Human Approval / Challenge Banner */}
      {interventions?.current_active ? (
        <div className="p-6 rounded-2xl bg-amber-500/15 border border-amber-500/40 shadow-lg space-y-4 animate-pulse">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-6 h-6 text-amber-400 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono text-[10px] uppercase font-bold">
                  {interventions.current_active.obstacle_type} Barrier Enforced
                </span>
                <h3 className="text-base font-semibold text-white">
                  Active Human Intervention Required
                </h3>
                <p className="text-xs text-amber-200/90 leading-relaxed max-w-2xl">
                  {interventions.current_active.message}
                </p>
                <div className="text-[11px] font-mono text-amber-300/80 truncate max-w-xl">
                  Target URL: {interventions.current_active.url}
                </div>
              </div>
            </div>

            <span className="text-xs font-mono text-amber-400">
              {new Date(interventions.current_active.timestamp * 1000).toLocaleTimeString()}
            </span>
          </div>

          <div className="pt-2 flex flex-col sm:flex-row items-center gap-3">
            <input
              type="text"
              value={resolutionNotes}
              onChange={(e) => setResolutionNotes(e.target.value)}
              placeholder="Operator notes (e.g. Completed manual CAPTCHA in browser)"
              className="flex-1 px-3 py-2 rounded-xl bg-nexus-950 border border-nexus-800 text-xs text-slate-200 focus:outline-none focus:border-amber-400"
            />
            <button
              onClick={handleResolve}
              disabled={resolving}
              className="px-5 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-nexus-950 font-bold text-xs shrink-0 transition-all flex items-center gap-2"
            >
              <UserCheck className="w-4 h-4" />
              <span>{resolving ? 'Resolving...' : 'Authorize & Resolve'}</span>
            </button>
          </div>
        </div>
      ) : (
        <div className="p-4 rounded-xl bg-nexus-900 border border-nexus-800/80 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2 text-slate-300">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span className="font-medium">No pending human interventions or blocked challenges</span>
          </div>
          <button
            onClick={loadSafety}
            className="p-1 rounded text-slate-400 hover:text-slate-200"
            title="Check active barriers"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      )}

      {/* Active Security Boundaries Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Read-Only Mode Policy */}
        <div className="p-5 rounded-2xl bg-nexus-900 border border-nexus-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-white">Read-Only Guard</span>
            <span className="px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 font-mono text-[10px] font-bold">
              {safety?.read_only_mode ? 'ENFORCED' : 'OFF'}
            </span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Blocks arbitrary form submissions, payments, purchase clicks, password changes, and deletes. Prevents irreversible actions.
          </p>
        </div>

        {/* SSRF & Private IP Policy */}
        <div className="p-5 rounded-2xl bg-nexus-900 border border-nexus-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-white">SSRF &amp; Loopback Shield</span>
            <span className="px-2 py-0.5 rounded-full bg-cyan-500/15 text-cyan-400 font-mono text-[10px] font-bold">
              {safety?.block_private_ips ? 'PROTECTED' : 'OFF'}
            </span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Blocks private subnets (10.0.0.0/8, 192.168.0.0/16, 127.0.0.1, 169.254.0.0/16 metadata endpoints) and internal ports.
          </p>
        </div>

        {/* Anti-Bot / CAPTCHA Protocol */}
        <div className="p-5 rounded-2xl bg-nexus-900 border border-nexus-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-white">Anti-Bot Handling</span>
            <span className="px-2 py-0.5 rounded-full bg-indigo-500/15 text-indigo-400 font-mono text-[10px] font-bold">
              SAFE PAUSE
            </span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Detects Cloudflare Turnstile, reCAPTCHA, and login walls. Pauses execution safely without solving or evading.
          </p>
        </div>
      </div>

      {/* Security Classifications Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Consequential Action Triggers */}
        <div className="p-5 rounded-2xl bg-nexus-900 border border-nexus-800 space-y-3">
          <div className="flex items-center gap-2 text-slate-300">
            <Ban className="w-4 h-4 text-rose-400" />
            <h3 className="text-xs font-semibold uppercase tracking-wider">
              Consequential Click Keywords
            </h3>
          </div>
          <p className="text-xs text-slate-400">
            Buttons or links containing these action triggers require human confirmation before dispatch:
          </p>
          <div className="flex flex-wrap gap-1.5 pt-1">
            {safety?.consequential_action_triggers.map((kw, i) => (
              <span key={i} className="px-2 py-1 rounded-lg bg-nexus-950 border border-nexus-800 text-rose-300 font-mono text-[11px]">
                {kw}
              </span>
            ))}
          </div>
        </div>

        {/* Sensitive Form Input Keywords */}
        <div className="p-5 rounded-2xl bg-nexus-900 border border-nexus-800 space-y-3">
          <div className="flex items-center gap-2 text-slate-300">
            <Lock className="w-4 h-4 text-amber-400" />
            <h3 className="text-xs font-semibold uppercase tracking-wider">
              Sensitive Input Guard
            </h3>
          </div>
          <p className="text-xs text-slate-400">
            Form fields matching these keywords are blocked from autonomous typing:
          </p>
          <div className="flex flex-wrap gap-1.5 pt-1">
            {safety?.sensitive_form_input_keywords.map((kw, i) => (
              <span key={i} className="px-2 py-1 rounded-lg bg-nexus-950 border border-nexus-800 text-amber-300 font-mono text-[11px]">
                {kw}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Historical Interventions Log */}
      <div className="p-5 rounded-2xl bg-nexus-900 border border-nexus-800 space-y-4">
        <h3 className="text-sm font-semibold text-white">Historical Security Events</h3>
        {interventions?.history && interventions.history.length > 0 ? (
          <div className="space-y-2">
            {interventions.history.map((h, idx) => (
              <div key={idx} className="p-3 rounded-xl bg-nexus-950 border border-nexus-800 text-xs flex items-center justify-between">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2 font-mono">
                    <span className="font-semibold text-slate-200">{h.obstacle_type}</span>
                    <span className="text-[10px] text-slate-400">
                      {new Date(h.timestamp * 1000).toLocaleString()}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-400 truncate max-w-xl">{h.url}</div>
                </div>
                <span className={`px-2 py-0.5 rounded font-mono text-[10px] ${
                  h.resolved ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-300'
                }`}>
                  {h.resolved ? 'RESOLVED' : 'PENDING'}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div className="py-8 text-center text-xs text-slate-400 border border-dashed border-nexus-800 rounded-xl">
            No security barrier interventions recorded in this session.
          </div>
        )}
      </div>
    </div>
  );
};
