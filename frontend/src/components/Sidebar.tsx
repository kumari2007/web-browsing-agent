import React from 'react';
import { 
  LayoutDashboard, 
  PlusCircle, 
  Globe, 
  History, 
  Database, 
  Brain, 
  BarChart3, 
  ShieldAlert, 
  Settings, 
  ChevronLeft, 
  ChevronRight,
  Bot
} from 'lucide-react';

export type NavSection = 
  | 'overview' 
  | 'new-task' 
  | 'live' 
  | 'history' 
  | 'knowledge' 
  | 'memory' 
  | 'analytics' 
  | 'safety' 
  | 'settings';

interface SidebarProps {
  currentSection: NavSection;
  onSelectSection: (section: NavSection) => void;
  collapsed: boolean;
  onToggleCollapsed: () => void;
  activeTaskId?: string | null;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentSection,
  onSelectSection,
  collapsed,
  onToggleCollapsed,
  activeTaskId
}) => {
  const navItems = [
    { id: 'overview' as NavSection, label: 'Overview', icon: LayoutDashboard },
    { id: 'new-task' as NavSection, label: 'New Task', icon: PlusCircle, highlight: true },
    { id: 'live' as NavSection, label: 'Live Browser', icon: Globe, hasPulse: !!activeTaskId },
    { id: 'history' as NavSection, label: 'Task History', icon: History },
    { id: 'knowledge' as NavSection, label: 'Knowledge Base', icon: Database },
    { id: 'memory' as NavSection, label: 'Experience Memory', icon: Brain },
    { id: 'analytics' as NavSection, label: 'Analytics', icon: BarChart3 },
    { id: 'safety' as NavSection, label: 'Safety Center', icon: ShieldAlert },
    { id: 'settings' as NavSection, label: 'Settings', icon: Settings },
  ];

  return (
    <aside 
      className={`fixed top-0 left-0 h-screen z-30 flex flex-col bg-nexus-900 border-r border-nexus-800 transition-all duration-300 ${
        collapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-nexus-800/80">
        <div className="flex items-center gap-3 overflow-hidden cursor-pointer" onClick={() => onSelectSection('overview')}>
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-600 via-indigo-600 to-cyan-400 p-[1.5px] shrink-0 shadow-lg shadow-cyan-500/10">
            <div className="w-full h-full bg-nexus-950 rounded-[10px] flex items-center justify-center">
              <Bot className="w-5 h-5 text-cyan-400" />
            </div>
          </div>
          {!collapsed && (
            <div className="flex flex-col">
              <span className="font-bold tracking-wider text-base bg-gradient-to-r from-cyan-300 via-white to-indigo-300 bg-clip-text text-transparent">
                NEXUS
              </span>
              <span className="text-[10px] text-slate-400 uppercase tracking-widest font-mono">
                Web Agent 2.0
              </span>
            </div>
          )}
        </div>

        <button 
          onClick={onToggleCollapsed}
          className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-nexus-800 transition-colors"
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Navigation List */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1.5 scrollbar-thin scrollbar-thumb-nexus-800">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentSection === item.id;

          return (
            <button
              key={item.id}
              onClick={() => onSelectSection(item.id)}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all group relative ${
                isActive 
                  ? 'bg-gradient-to-r from-cyan-500/15 to-indigo-500/10 text-cyan-300 border border-cyan-500/30 shadow-sm shadow-cyan-500/10' 
                  : 'text-slate-400 hover:text-slate-200 hover:bg-nexus-850/80 border border-transparent'
              }`}
            >
              <div className="relative shrink-0">
                <Icon className={`w-5 h-5 transition-transform group-hover:scale-110 ${
                  isActive ? 'text-cyan-400' : 'text-slate-400 group-hover:text-slate-200'
                }`} />
                {item.hasPulse && (
                  <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping" />
                )}
              </div>

              {!collapsed && (
                <span className="truncate flex-1 text-left">
                  {item.label}
                </span>
              )}

              {isActive && (
                <span className="absolute right-2 w-1.5 h-4 bg-cyan-400 rounded-full" />
              )}
            </button>
          );
        })}
      </nav>

      {/* System Status Footer */}
      {!collapsed && (
        <div className="p-4 border-t border-nexus-800/80 bg-nexus-950/40">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              Core Engine
            </span>
            <span className="font-mono text-[10px] text-cyan-400">RAG + Browser</span>
          </div>
          <div className="text-[11px] text-slate-500 truncate">
            Playwright &amp; Chroma/SQLite
          </div>
        </div>
      )}
    </aside>
  );
};
