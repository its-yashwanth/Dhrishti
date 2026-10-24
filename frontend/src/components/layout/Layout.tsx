import React, { useState, useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { DrishtiAPI } from '../../services/api';
import { DrishtiAnalysisResult } from '../../types/drishti';

export const Layout: React.FC = () => {
  const [currentScenario, setCurrentScenario] = useState<DrishtiAnalysisResult | undefined>();
  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(() => {
    try {
      const saved = localStorage.getItem('drishti_sidebar_open');
      return saved !== null ? JSON.parse(saved) : true;
    } catch {
      return true;
    }
  });
  const location = useLocation();

  const toggleSidebar = () => {
    setIsSidebarOpen((prev) => {
      const next = !prev;
      try {
        localStorage.setItem('drishti_sidebar_open', JSON.stringify(next));
      } catch {
        // Ignore
      }
      return next;
    });
  };

  // Keyboard shortcut Ctrl+B or Cmd+B to toggle sidebar
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'b') {
        e.preventDefault();
        toggleSidebar();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const loadCurrent = async () => {
    try {
      const res = await DrishtiAPI.getLatestAnalysis();
      setCurrentScenario(res);
    } catch {
      // Ignore
    }
  };

  useEffect(() => {
    loadCurrent();
  }, [location.pathname]);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#070a12] text-slate-100 font-sans">
      {/* Left Collapsible Sliding Sidebar */}
      <Sidebar isOpen={isSidebarOpen} onToggle={toggleSidebar} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Header */}
        <Header
          currentScenario={currentScenario}
          onRefresh={loadCurrent}
          isSidebarOpen={isSidebarOpen}
          onToggleSidebar={toggleSidebar}
        />

        {/* Scrollable Page Body */}
        <main className="flex-1 overflow-y-auto px-6 py-6 bg-gradient-to-b from-[#0a0f1d]/50 via-[#070a12] to-[#070a12]">
          <div className="max-w-7xl mx-auto space-y-6">
            <Outlet context={{ currentScenario, refreshScenario: loadCurrent }} />
          </div>
        </main>
      </div>
    </div>
  );
};
