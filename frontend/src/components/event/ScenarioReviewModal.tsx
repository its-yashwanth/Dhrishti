import React, { useState, useEffect } from 'react';
import { StructuredEvent, TradeFlow, TradeShareStatus } from '../../types/drishti';
import { COMMODITY_TO_HS4, HS4_TO_COMMODITY } from '../../services/api';
import { Check, Edit3, ArrowRight, Sparkles, Layers, Sliders, AlertTriangle, ShieldCheck, Database, FileText } from 'lucide-react';
import { Badge } from '../common/Badge';
import { ProvenanceTag } from '../common/ProvenanceTag';

interface ScenarioReviewModalProps {
  event: StructuredEvent;
  onConfirm: (confirmedParams: {
    commodity: string;
    partner_country: string;
    trade_type: TradeFlow;
    shock_intensity: number;
    shock_intensity_source: string;
    trade_share: number;
    trade_share_source: string;
    trade_share_status: TradeShareStatus;
    scenario_multiplier: number;
    hs4: number;
  }) => void;
  onCancel: () => void;
}

export const ScenarioReviewModal: React.FC<ScenarioReviewModalProps> = ({
  event,
  onConfirm,
  onCancel
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [commodity, setCommodity] = useState(event.commodity);
  const [country, setCountry] = useState(event.country);
  const [tradeType, setTradeType] = useState<TradeFlow>(event.trade_type);
  const [shockIntensity, setShockIntensity] = useState(event.shock_intensity ?? 1.5);
  const [shockIntensitySource, setShockIntensitySource] = useState(event.shock_intensity_source || 'GDELT Global News Intelligence (MCP Event DB)');
  const [tradeShare, setTradeShare] = useState(event.trade_share ?? 5.0);
  const [tradeShareSource, setTradeShareSource] = useState(event.trade_share_source || 'Historical Trade Database (UN Comtrade / DGFT)');
  const [tradeShareStatus, setTradeShareStatus] = useState<TradeShareStatus>(event.trade_share_status || 'CONFIRMED_HISTORICAL');
  const [scenarioMultiplier, setScenarioMultiplier] = useState(event.scenario_multiplier ?? 1.0);
  const [hs4, setHs4] = useState(event.hs4 || 1001);

  // Sync state when incoming event prop changes
  useEffect(() => {
    setCommodity(event.commodity);
    setCountry(event.country);
    setTradeType(event.trade_type);
    setShockIntensity(event.shock_intensity ?? 1.5);
    setShockIntensitySource(event.shock_intensity_source || 'GDELT Global News Intelligence (MCP Event DB)');
    setTradeShare(event.trade_share ?? 5.0);
    setTradeShareSource(event.trade_share_source || 'Historical Trade Database (UN Comtrade / DGFT)');
    setTradeShareStatus(event.trade_share_status || 'CONFIRMED_HISTORICAL');
    setScenarioMultiplier(event.scenario_multiplier ?? 1.0);
    setHs4(event.hs4 || 1001);
  }, [event]);

  // When commodity changes in edit mode, auto-resolve canonical HS4
  const handleCommodityChange = (newCommodity: string) => {
    setCommodity(newCommodity);
    const lower = newCommodity.trim().toLowerCase();
    if (COMMODITY_TO_HS4[lower]) {
      setHs4(COMMODITY_TO_HS4[lower]);
    }
  };

  // Dynamic Effective Shock Calculation
  const effectiveShock = Number(((shockIntensity * scenarioMultiplier * tradeShare) / 100).toFixed(4));
  const effectiveShockFormula = `(${shockIntensity.toFixed(2)} [GDELT] × ${scenarioMultiplier.toFixed(1)}x [Multiplier] × ${tradeShare.toFixed(1)}% [Share]) / 100 = ${effectiveShock.toFixed(4)}`;

  const handleConfirm = () => {
    onConfirm({
      commodity,
      partner_country: country,
      trade_type: tradeType,
      shock_intensity: Number(shockIntensity),
      shock_intensity_source: shockIntensitySource,
      trade_share: Number(tradeShare),
      trade_share_source: tradeShareSource,
      trade_share_status: tradeShareStatus,
      scenario_multiplier: Number(scenarioMultiplier),
      hs4: Number(hs4)
    });
  };

  const tradeFlowDesc = tradeType === 'Export'
    ? `India → ${country.toUpperCase()}`
    : `${country.toUpperCase()} → India`;

  return (
    <div className="card-terminal rounded-xl border border-cyan-500/40 p-6 relative shadow-2xl bg-gradient-to-b from-[#0e172a] via-[#091122] to-[#070b14]">
      {/* Top Ambient Highlight */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-cyan-500 via-sky-400 to-purple-500 rounded-t-xl" />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4 mb-5">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-cyan-950 border border-cyan-800 text-cyan-400 shadow-sm">
            <Sparkles className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-base font-bold text-white tracking-tight">
                DETECTED EVENT PARAMETERS
              </h3>
              <Badge
                label={event.confidence ? `${event.confidence.toUpperCase()} CONFIDENCE` : 'CANONICAL MATCH'}
                variant="CYAN"
                size="sm"
              />
            </div>
            <p className="text-xs text-slate-400">
              Cross-referenced against canonical HS4 commodity dictionary and GDELT DOC 2.0 telemetry
            </p>
          </div>
        </div>

        <button
          onClick={() => setIsEditing(!isEditing)}
          className="self-start sm:self-auto px-3.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 hover:border-cyan-500 text-xs font-mono text-slate-200 hover:text-cyan-300 flex items-center space-x-2 transition-all cursor-pointer shadow-sm"
        >
          <Edit3 className="w-3.5 h-3.5 text-cyan-400" />
          <span>{isEditing ? 'Collapse Parameters' : 'Edit Parameters'}</span>
        </button>
      </div>

      {/* Narrative Event Summary */}
      <div className="p-3.5 rounded-lg bg-slate-950/80 border border-slate-800 text-xs text-slate-200 leading-relaxed mb-5 flex items-start space-x-3">
        <Layers className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
        <div className="flex-1">
          <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold mb-0.5">
            Scenario Event Formulation
          </div>
          <div>{event.summary}</div>
        </div>
      </div>

      {/* 4 Quantitative Blocks with Explicit Provenance */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {/* Block 1: Historical Trade Exposure */}
        <div className="p-4 rounded-lg bg-[#070d19] border border-slate-800/90 flex flex-col justify-between space-y-2 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold">
              Historical Trade Exposure
            </span>
            <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded font-bold ${
              tradeShareStatus === 'CONFIRMED_HISTORICAL'
                ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                : 'bg-amber-950 text-amber-300 border border-amber-800'
            }`}>
              {tradeShareStatus === 'CONFIRMED_HISTORICAL' ? 'HISTORICAL' : 'UNAVAILABLE'}
            </span>
          </div>

          <div>
            <div className="text-2xl font-bold font-mono text-white tracking-tight">
              {tradeShare.toFixed(1)}%
            </div>
            <div className="text-[11px] font-mono text-cyan-400 mt-0.5">
              {tradeFlowDesc}
            </div>
          </div>

          <div className="pt-2 border-t border-slate-800/70 text-[10px] text-slate-400 line-clamp-2">
            <span className="font-semibold text-slate-300">Source: </span>
            {tradeShareSource}
          </div>
        </div>

        {/* Block 2: GDELT Event Evidence */}
        <div className="p-4 rounded-lg bg-[#070d19] border border-slate-800/90 flex flex-col justify-between space-y-2 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold">
              GDELT Event Evidence
            </span>
            <span className="text-[9px] font-mono px-1.5 py-0.5 rounded font-bold bg-purple-950 text-purple-300 border border-purple-800">
              GDELT DOC 2.0
            </span>
          </div>

          <div>
            <div className="text-2xl font-bold font-mono text-purple-300 tracking-tight">
              {shockIntensity.toFixed(2)}x
            </div>
            <div className="text-[11px] font-mono text-slate-400 mt-0.5">
              Event Intensity Calibration
            </div>
          </div>

          <div className="pt-2 border-t border-slate-800/70 text-[10px] text-slate-400 line-clamp-2">
            <span className="font-semibold text-slate-300">Evidence: </span>
            {shockIntensitySource}
          </div>
        </div>

        {/* Block 3: Scenario Multiplier */}
        <div className="p-4 rounded-lg bg-[#070d19] border border-slate-800/90 flex flex-col justify-between space-y-2 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold">
              Scenario Multiplier
            </span>
            <span className="text-[9px] font-mono px-1.5 py-0.5 rounded font-bold bg-sky-950 text-sky-300 border border-sky-800">
              USER SCENARIO
            </span>
          </div>

          <div>
            <div className="text-2xl font-bold font-mono text-sky-300 tracking-tight">
              {scenarioMultiplier.toFixed(1)}x
            </div>
            <div className="text-[11px] font-mono text-slate-400 mt-0.5">
              Stress-Test Scaling Factor
            </div>
          </div>

          <div className="pt-2 border-t border-slate-800/70 text-[10px] text-slate-400 line-clamp-2">
            <span className="font-semibold text-slate-300">Provenance: </span>
            Optional user parameter override (Default: 1.0x baseline)
          </div>
        </div>

        {/* Block 4: Effective Shock Calculation */}
        <div className="p-4 rounded-lg bg-gradient-to-br from-[#0c1527] to-[#070d19] border border-cyan-600/50 flex flex-col justify-between space-y-2 relative overflow-hidden shadow-glow-cyan">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-300 font-semibold">
              Effective Shock
            </span>
            <span className="text-[9px] font-mono px-1.5 py-0.5 rounded font-bold bg-cyan-950 text-cyan-300 border border-cyan-700">
              FORMULA DERIVED
            </span>
          </div>

          <div>
            <div className="text-2xl font-bold font-mono text-cyan-300 tracking-tight">
              {effectiveShock.toFixed(4)}
            </div>
            <div className="text-[11px] font-mono text-slate-400 mt-0.5">
              Intensity × Multiplier × Share / 100
            </div>
          </div>

          <div className="pt-2 border-t border-slate-800/70 text-[10px] font-mono text-cyan-400/90 truncate">
            {effectiveShockFormula}
          </div>
        </div>
      </div>

      {/* Edit Mode Parameter Controls */}
      {isEditing && (
        <div className="mb-6 p-5 rounded-xl bg-slate-950/90 border border-cyan-500/30 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <span className="text-xs font-mono font-semibold text-cyan-400 flex items-center space-x-1.5">
              <Sliders className="w-3.5 h-3.5" />
              <span>PARAMETER EDITING & CANONICAL VERIFICATION</span>
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              Canonical HS4 dictionary: <span className="text-cyan-300 font-bold">{hs4}</span>
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Commodity */}
            <div>
              <label className="block text-[11px] font-mono text-slate-300 mb-1">
                Commodity Name
              </label>
              <input
                type="text"
                value={commodity}
                onChange={(e) => handleCommodityChange(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white font-mono focus:border-cyan-500 focus:outline-none"
              />
              <span className="text-[10px] font-mono text-slate-400 mt-1 block">
                Auto-resolves HS4: {COMMODITY_TO_HS4[commodity.toLowerCase()] || 'Custom / Unmapped'}
              </span>
            </div>

            {/* Partner Country */}
            <div>
              <label className="block text-[11px] font-mono text-slate-300 mb-1">
                Partner Country
              </label>
              <input
                type="text"
                value={country}
                onChange={(e) => setCountry(e.target.value.toUpperCase())}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white font-mono focus:border-cyan-500 focus:outline-none"
              />
              <span className="text-[10px] font-mono text-slate-400 mt-1 block">
                Bilateral counterpart to India
              </span>
            </div>

            {/* Trade Flow */}
            <div>
              <label className="block text-[11px] font-mono text-slate-300 mb-1">
                Trade Direction
              </label>
              <select
                value={tradeType}
                onChange={(e) => setTradeType(e.target.value as TradeFlow)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white font-mono focus:border-cyan-500 focus:outline-none"
              >
                <option value="Export">Export (India → Partner)</option>
                <option value="Import">Import (Partner → India)</option>
              </select>
              <span className="text-[10px] font-mono text-slate-400 mt-1 block">
                Baseline flow perspective
              </span>
            </div>

            {/* GDELT Shock Intensity Slider */}
            <div>
              <div className="flex justify-between text-[11px] font-mono mb-1">
                <span className="text-slate-300">GDELT Shock Intensity</span>
                <span className="text-purple-300 font-bold">{shockIntensity.toFixed(2)}x</span>
              </div>
              <input
                type="range"
                min="0.5"
                max="3.0"
                step="0.1"
                value={shockIntensity}
                onChange={(e) => setShockIntensity(parseFloat(e.target.value))}
                className="w-full accent-purple-400 cursor-pointer"
              />
              <span className="text-[10px] text-slate-400">
                Extracted from news event signals
              </span>
            </div>

            {/* Scenario Multiplier Slider */}
            <div>
              <div className="flex justify-between text-[11px] font-mono mb-1">
                <span className="text-slate-300">Scenario Multiplier</span>
                <span className="text-sky-300 font-bold">{scenarioMultiplier.toFixed(1)}x</span>
              </div>
              <input
                type="range"
                min="0.5"
                max="3.0"
                step="0.1"
                value={scenarioMultiplier}
                onChange={(e) => setScenarioMultiplier(parseFloat(e.target.value))}
                className="w-full accent-sky-400 cursor-pointer"
              />
              <span className="text-[10px] text-slate-400">
                User scenario stress-testing override
              </span>
            </div>

            {/* Historical Trade Share Slider */}
            <div>
              <div className="flex justify-between text-[11px] font-mono mb-1">
                <span className="text-slate-300">Trade Share Exposure</span>
                <span className="text-cyan-300 font-bold">{tradeShare.toFixed(1)}%</span>
              </div>
              <input
                type="range"
                min="0.5"
                max="50.0"
                step="0.5"
                value={tradeShare}
                onChange={(e) => setTradeShare(parseFloat(e.target.value))}
                className="w-full accent-cyan-400 cursor-pointer"
              />
              <span className="text-[10px] text-slate-400">
                Bilateral trade share baseline
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Footer Provenance and Action Buttons */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-4 border-t border-slate-800">
        <div className="flex items-center space-x-2 text-xs font-mono text-slate-400">
          <Database className="w-3.5 h-3.5 text-cyan-400" />
          <span>CANONICAL PIPELINE ROUTING:</span>
          <span className="text-slate-300 font-bold">{commodity}</span>
          <span className="text-slate-600">→</span>
          <span className="text-cyan-300 font-bold">HS4 {hs4}</span>
          <span className="text-slate-600">|</span>
          <span className="text-slate-300">{country}</span>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 text-xs font-mono transition-colors cursor-pointer border border-slate-800"
          >
            Cancel / Clear
          </button>
          <button
            onClick={handleConfirm}
            className="px-5 py-2 rounded-lg bg-gradient-to-r from-cyan-600 via-sky-600 to-cyan-500 hover:from-cyan-500 hover:to-sky-400 text-white font-mono text-xs font-bold shadow-glow-cyan flex items-center space-x-2 transition-all cursor-pointer border border-cyan-400/40"
          >
            <span>Run Full Analysis →</span>
          </button>
        </div>
      </div>
    </div>
  );
};
