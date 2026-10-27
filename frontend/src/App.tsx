import React, { useState, useEffect } from 'react';
import { Sidebar, NavSection } from './components/Sidebar';
import { TopBar } from './components/TopBar';
import { OverviewView } from './views/OverviewView';
import { NewTaskView } from './views/NewTaskView';
import { LiveBrowserView } from './views/LiveBrowserView';
import { TaskHistoryView } from './views/TaskHistoryView';
import { KnowledgeBaseView } from './views/KnowledgeBaseView';
import { ExperienceMemoryView } from './views/ExperienceMemoryView';
import { AnalyticsView } from './views/AnalyticsView';
import { SafetyCenterView } from './views/SafetyCenterView';
import { SettingsView } from './views/SettingsView';
import { api } from './services/api';

export const App: React.FC = () => {
  const [currentSection, setCurrentSection] = useState<NavSection>('overview');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
  const [selectedHistoryTaskId, setSelectedHistoryTaskId] = useState<string | null>(null);
  const [serverOnline, setServerOnline] = useState(true);

  // Periodic health check
  useEffect(() => {
    const checkHealth = async () => {
      try {
        await api.getHealth();
        setServerOnline(true);
      } catch {
        setServerOnline(false);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleTaskStarted = (taskId: string) => {
    setActiveTaskId(taskId);
    setSelectedHistoryTaskId(taskId);
  };

  const renderActiveView = () => {
    switch (currentSection) {
      case 'overview':
        return (
          <OverviewView 
            onNavigate={setCurrentSection} 
            onSelectTask={(id) => {
              setSelectedHistoryTaskId(id);
              setCurrentSection('history');
            }} 
          />
        );
      case 'new-task':
        return (
          <NewTaskView 
            onTaskStarted={handleTaskStarted} 
            onNavigate={setCurrentSection} 
          />
        );
      case 'live':
        return (
          <LiveBrowserView 
            activeTaskId={activeTaskId} 
            onNavigate={setCurrentSection}
            onSelectTask={(id) => {
              setSelectedHistoryTaskId(id);
              setCurrentSection('history');
            }} 
          />
        );
      case 'history':
        return (
          <TaskHistoryView 
            selectedTaskId={selectedHistoryTaskId} 
            onSelectTask={setSelectedHistoryTaskId} 
          />
        );
      case 'knowledge':
        return <KnowledgeBaseView />;
      case 'memory':
        return <ExperienceMemoryView />;
      case 'analytics':
        return <AnalyticsView />;
      case 'safety':
        return <SafetyCenterView />;
      case 'settings':
        return <SettingsView />;
      default:
        return (
          <OverviewView 
            onNavigate={setCurrentSection} 
            onSelectTask={setSelectedHistoryTaskId} 
          />
        );
    }
  };

  return (
    <div className="min-h-screen bg-nexus-950 text-slate-100 flex">
      {/* Collapsible Left Sidebar */}
      <Sidebar
        currentSection={currentSection}
        onSelectSection={setCurrentSection}
        collapsed={sidebarCollapsed}
        onToggleCollapsed={() => setSidebarCollapsed(!sidebarCollapsed)}
        activeTaskId={activeTaskId}
      />

      {/* Main Container */}
      <div 
        className={`flex-1 flex flex-col min-w-0 transition-all duration-300 ${
          sidebarCollapsed ? 'pl-20' : 'pl-64'
        }`}
      >
        {/* Top Header Bar */}
        <TopBar
          currentSection={currentSection}
          onNavigate={setCurrentSection}
          activeTaskId={activeTaskId}
          serverOnline={serverOnline}
        />

        {/* Workspace Body */}
        <main className="flex-1 p-6 md:p-8 max-w-7xl mx-auto w-full">
          {renderActiveView()}
        </main>
      </div>
    </div>
  );
};

export default App;
