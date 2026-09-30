import React, { useEffect, useState } from 'react';
import { Shield, Activity, Radio, Cpu, RefreshCw } from 'lucide-react';
import { DrishtiAPI } from '../../services/api';
import { DrishtiAnalysisResult } from '../../types/drishti';

interface HeaderProps {
  currentScenario?: DrishtiAnalysisResult;
  onRefresh?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ currentScenario, onRefresh }) => {
  const [apiHealth, setApiHealth] = useState<{ status: string; latencyMs: number }>({
    status: 'checking',
    latencyMs: 0
  });

  useEffect(() => {
    let mounted = true;
    const check = async () => {
      const res = await DrishtiAPI.checkHealth();
      if (mounted) {
        setApiHealth({
          status: res.status === 'online' ? 'CONNECTED' : 'LOCAL ENGINE',
          latencyMs: res.latencyMs
        });
      }
    };
    check();
    const interval = setInterval(check, 15000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const scenarioDesc = currentScenario?.scenario_name || 'Wheat Export Disruption (India → Russia)';

  return (
    <header className="h-16 border-b border-slate-800 bg-[#070a12]/95 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-40">
      {/* Brand & Subtitle */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-cyan-500/20 via-sky-600/30 to-purple-600/20 border border-cyan-500/40 flex items-center justify-center shadow-glow-cyan">
            <Shield className="w-5 h-5 text-cyan-400" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-extrabold tracking-wider text-lg text-white font-mono">DRISHTI</span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950/80 border border-cyan-800 text-cyan-300 font-semibold uppercase">
                RESEARCH v2.4
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-medium tracking-tight">
              Exposure-Aware Geopolitical Impact Assessment Framework
            </p>
          </div>
        </div>
      </div>

      {/* Active Scenario Indicator */}
      <div className="hidden lg:flex items-center space-x-3 px-3 py-1.5 rounded-md bg-slate-900/80 border border-slate-800 text-xs">
        <div className="flex items-center space-x-2 text-slate-400">
          <Radio className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
          <span>Active Scenario:</span>
        </div>
        <span className="font-mono font-medium text-slate-200 truncate max-w-xs xl:max-w-md">
          {scenarioDesc}
        </span>
      </div>

      {/* System Status Indicators */}
      <div className="flex items-center space-x-4 text-xs">
        {/* Core status */}
        <div className="hidden sm:flex items-center space-x-2 px-2.5 py-1 rounded bg-slate-900 border border-slate-800">
          <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-glow-green animate-pulse" />
          <span className="text-slate-300 font-mono text-[11px]">CORE READY</span>
        </div>

        {/* API connection status */}
        <div className="flex items-center space-x-2 px-2.5 py-1 rounded bg-slate-900 border border-slate-800">
          <Activity className="w-3.5 h-3.5 text-cyan-400" />
          <span className="font-mono text-[11px] text-slate-300">
            {apiHealth.status}
          </span>
          <span className="text-[10px] text-slate-500 font-mono">
            {apiHealth.latencyMs}ms
          </span>
        </div>

        {onRefresh && (
          <button
            onClick={onRefresh}
            title="Refresh Analysis State"
            className="p-1.5 text-slate-400 hover:text-cyan-300 hover:bg-slate-800/80 rounded transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        )}
      </div>
    </header>
  );
};
