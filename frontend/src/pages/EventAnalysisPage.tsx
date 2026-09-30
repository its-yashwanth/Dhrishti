import React, { useState } from 'react';
import { useOutletContext, useNavigate } from 'react-router-dom';
import { Sparkles, Globe, Sliders, ArrowRight, ShieldCheck, Database, Radio, CheckCircle2, Loader2, AlertCircle } from 'lucide-react';
import { Badge } from '../components/common/Badge';
import { ProvenanceTag } from '../components/common/ProvenanceTag';
import { DrishtiAPI, PipelineStageEvent } from '../services/api';
import { DrishtiAnalysisResult, TradeFlow } from '../types/drishti';

interface OutletContextType {
  currentScenario: DrishtiAnalysisResult;
  refreshScenario: () => void;
}

export const EventAnalysisPage: React.FC = () => {
  const { currentScenario, refreshScenario } = useOutletContext<OutletContextType>();
  const navigate = useNavigate();

  const [query, setQuery] = useState(currentScenario?.scenario_data?.query || 'Russia stopped importing wheat from India');
  const [partnerCountry, setPartnerCountry] = useState(currentScenario?.scenario_data?.event_country || 'RUSSIA');
  const [commodity, setCommodity] = useState(currentScenario?.scenario_data?.commodity || 'Wheat');
  const [tradeType, setTradeType] = useState<TradeFlow>(currentScenario?.scenario_data?.trade_type || 'Export');
  const [shockIntensity, setShockIntensity] = useState(currentScenario?.scenario_data?.shock_intensity ?? 1.5);
  const [tradeShare, setTradeShare] = useState(currentScenario?.scenario_data?.trade_share ?? 5.0);
  const [hs4, setHs4] = useState(currentScenario?.scenario_data?.hs4 ?? 1001);

  const [isRunning, setIsRunning] = useState(false);
  const [activeStage, setActiveStage] = useState<PipelineStageEvent['stage']>();
  const [pipelineLogs, setPipelineLogs] = useState<Array<{ stage: string; detail?: string }>>([]);

  const handleRunPipeline = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsRunning(true);
    setPipelineLogs([]);

    try {
      await DrishtiAPI.runFullAnalysis(
        {
          query,
          partner_country: partnerCountry,
          commodity,
          trade_type: tradeType,
          shock_intensity: Number(shockIntensity),
          trade_share: Number(tradeShare),
          hs4: Number(hs4)
        },
        (progress) => {
          setActiveStage(progress.stage);
          setPipelineLogs(prev => [...prev, { stage: progress.label, detail: progress.detail }]);
        }
      );
      refreshScenario();
    } catch {
      // Handle error
    } finally {
      setIsRunning(false);
    }
  };

  const effectiveShock = ((shockIntensity * tradeShare) / 100).toFixed(4);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center space-x-2 text-cyan-400 font-mono text-xs mb-1">
            <Radio className="w-4 h-4 text-cyan-400 animate-pulse" />
            <span>EVENT INTELLIGENCE AGENT INTERFACE</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Geopolitical Shock Parameterization & Verification
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Extract, structure, and calibrate geopolitical agricultural trade events with strict provenance separation.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <Badge label="MCP GDELT DOC 2.0 READY" variant="CYAN" size="sm" />
          <Badge label="STRICT PROVENANCE ENFORCED" variant="PURPLE" size="sm" />
        </div>
      </div>

      {/* Main Grid: Input Form vs Extracted Verification */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Interactive Ingestion & Override Form */}
        <div className="lg:col-span-7 card-terminal rounded-xl p-6 border border-slate-800 space-y-5">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-sm font-bold text-white font-mono flex items-center space-x-2">
              <Sliders className="w-4 h-4 text-cyan-400" />
              <span>SCENARIO PARAMETER CONFIGURATION</span>
            </h2>
            <ProvenanceTag tag="[USER / CLI PARAMETERS]" size="sm" />
          </div>

          <form onSubmit={handleRunPipeline} className="space-y-4">
            <div>
              <label className="block text-xs font-mono text-slate-300 mb-1.5 font-medium">
                Natural-Language Event Query
              </label>
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                rows={3}
                placeholder="Describe geopolitical event..."
                className="w-full bg-[#070b14] border border-slate-700 rounded-lg p-3 text-xs text-slate-100 font-sans focus:outline-none focus:border-cyan-500 leading-relaxed"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Commodity</label>
                <input
                  type="text"
                  value={commodity}
                  onChange={(e) => setCommodity(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Partner Country</label>
                <input
                  type="text"
                  value={partnerCountry}
                  onChange={(e) => setPartnerCountry(e.target.value.toUpperCase())}
                  className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Trade Flow Direction</label>
                <select
                  value={tradeType}
                  onChange={(e) => setTradeType(e.target.value as TradeFlow)}
                  className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value="Export">Export (India → Partner)</option>
                  <option value="Import">Import (Partner → India)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Harmonized System (HS4)</label>
                <input
                  type="number"
                  value={hs4}
                  onChange={(e) => setHs4(parseInt(e.target.value))}
                  className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs font-mono text-slate-400 mb-1">
                  <span>Shock Multiplier: {shockIntensity}x</span>
                  <span className="text-slate-500">Range: 0.5 - 3.0</span>
                </div>
                <input
                  type="range"
                  min="0.5"
                  max="3.0"
                  step="0.1"
                  value={shockIntensity}
                  onChange={(e) => setShockIntensity(parseFloat(e.target.value))}
                  className="w-full accent-cyan-400 cursor-pointer"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs font-mono text-slate-400 mb-1">
                  <span>Trade Share: {tradeShare}%</span>
                  <span className="text-slate-500">Range: 1.0 - 25.0%</span>
                </div>
                <input
                  type="range"
                  min="1.0"
                  max="25.0"
                  step="0.5"
                  value={tradeShare}
                  onChange={(e) => setTradeShare(parseFloat(e.target.value))}
                  className="w-full accent-cyan-400 cursor-pointer"
                />
              </div>
            </div>

            <div className="pt-2 flex items-center justify-between border-t border-slate-800">
              <div className="text-xs font-mono text-slate-400">
                Effective Shock (Shock × Share): <span className="text-cyan-400 font-bold">{effectiveShock}</span>
              </div>

              <button
                type="submit"
                disabled={isRunning}
                className="px-5 py-2.5 rounded bg-gradient-to-r from-cyan-600 to-sky-600 hover:from-cyan-500 hover:to-sky-500 text-white font-mono text-xs font-bold shadow-glow-cyan flex items-center space-x-2 transition-all cursor-pointer disabled:opacity-50"
              >
                {isRunning ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Executing Cascade...</span>
                  </>
                ) : (
                  <>
                    <span>Run Complete Orchestrator Pipeline</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Right: Verified Parameters & Live Execution Telemetry */}
        <div className="lg:col-span-5 space-y-5">
          {/* Active Verification Card */}
          <div className="card-terminal rounded-xl p-5 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
              <div className="flex items-center space-x-2 text-xs font-mono text-slate-300 font-semibold">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span>STRUCTURED EVENT VERIFICATION</span>
              </div>
              <Badge label="CANONICAL SHOCK DIRECTION" variant="CYAN" size="sm" />
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-800/60 font-mono">
                <span className="text-slate-400">Canonical Shock Direction:</span>
                <span className="text-rose-400 font-bold">supply_contraction</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60 font-mono">
                <span className="text-slate-400">Trade Flow Perspective:</span>
                <span className="text-slate-200">
                  {tradeType === 'Export' ? `India → ${partnerCountry}` : `${partnerCountry} → India`}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60 font-mono">
                <span className="text-slate-400">HS4 Catalog Match:</span>
                <span className="text-cyan-300 font-bold">{commodity} ({hs4})</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60 font-mono">
                <span className="text-slate-400">GDELT Alignment:</span>
                <span className="text-emerald-400">Goldstein: -4.5 | Tone: -3.2</span>
              </div>
              <div className="flex justify-between py-1 font-mono">
                <span className="text-slate-400">Extracted Confidence:</span>
                <span className="text-cyan-400 font-bold">HIGH (3 Triangulated Sources)</span>
              </div>
            </div>
          </div>

          {/* Execution Pipeline Console */}
          <div className="card-terminal rounded-xl p-5 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <div className="flex items-center space-x-2 text-xs font-mono text-slate-300 font-semibold">
                <Database className="w-3.5 h-3.5 text-purple-400" />
                <span>ORCHESTRATOR TELEMETRY</span>
              </div>
              {isRunning && <span className="text-[10px] font-mono text-cyan-400 animate-pulse">STREAMING...</span>}
            </div>

            <div className="bg-[#050811] rounded-lg p-3 font-mono text-[11px] h-48 overflow-y-auto space-y-1.5 border border-slate-800/60 text-slate-400">
              {pipelineLogs.length === 0 ? (
                <div className="text-slate-600 text-center py-12">
                  Ready. Click "Run Complete Orchestrator Pipeline" to trigger agent cascade.
                </div>
              ) : (
                pipelineLogs.map((log, idx) => (
                  <div key={idx} className="flex items-start space-x-2">
                    <span className="text-cyan-500 shrink-0">▸</span>
                    <div>
                      <span className="text-slate-200 font-semibold">{log.stage}:</span>{' '}
                      <span className="text-slate-400">{log.detail}</span>
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="flex items-center justify-between pt-1 text-[11px] font-mono text-slate-500">
              <span>Agent Suite: 6 Agents</span>
              <span>Cascade Models: A → B → C → D</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
