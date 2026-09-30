import React, { useState } from 'react';
import { StructuredEvent, TradeFlow } from '../../types/drishti';
import { Check, Edit3, ArrowRight, ShieldAlert, Sparkles, Layers, Sliders } from 'lucide-react';
import { Badge } from '../common/Badge';
import { ProvenanceTag } from '../common/ProvenanceTag';

interface ScenarioReviewModalProps {
  event: StructuredEvent;
  onConfirm: (confirmedParams: {
    commodity: string;
    partner_country: string;
    trade_type: TradeFlow;
    shock_intensity: number;
    trade_share: number;
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
  const [tradeShare, setTradeShare] = useState(event.trade_share ?? 5.0);
  const [hs4, setHs4] = useState(event.hs4);

  const handleConfirm = () => {
    onConfirm({
      commodity,
      partner_country: country,
      trade_type: tradeType,
      shock_intensity: Number(shockIntensity),
      trade_share: Number(tradeShare),
      hs4: Number(hs4)
    });
  };

  const tradeFlowDesc = tradeType === 'Export'
    ? `India → ${country.toUpperCase()}`
    : `${country.toUpperCase()} → India`;

  return (
    <div className="card-terminal rounded-xl border border-cyan-500/40 p-6 relative shadow-2xl bg-gradient-to-b from-[#0e172a] to-[#070b14]">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-5">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded bg-cyan-950 border border-cyan-800 text-cyan-400">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-base font-bold text-white tracking-tight">
                DETECTED GEOPOLITICAL EVENT
              </h3>
              <Badge label={event.confidence.toUpperCase() + ' CONFIDENCE'} variant="CYAN" size="sm" />
            </div>
            <p className="text-xs text-slate-400">
              Extracted by Event Intelligence Agent & verified against GDELT / HS4 directory
            </p>
          </div>
        </div>

        <button
          onClick={() => setIsEditing(!isEditing)}
          className="px-3 py-1.5 rounded bg-slate-900 border border-slate-700 hover:border-slate-600 text-xs font-mono text-slate-300 flex items-center space-x-1.5 transition-colors cursor-pointer"
        >
          <Edit3 className="w-3.5 h-3.5 text-cyan-400" />
          <span>{isEditing ? 'View Summary' : 'Edit Parameters'}</span>
        </button>
      </div>

      {/* Summary Narrative */}
      <div className="p-3.5 rounded-lg bg-slate-900/70 border border-slate-800 text-xs text-slate-300 leading-relaxed mb-5">
        <div className="flex items-center space-x-1.5 text-cyan-400 font-mono text-[11px] font-semibold mb-1">
          <Layers className="w-3.5 h-3.5" />
          <span>SCENARIO SYNTHESIS</span>
        </div>
        {event.summary}
      </div>

      {/* Structured Parameters Grid */}
      {!isEditing ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="p-3 rounded bg-slate-950/60 border border-slate-800/80">
            <span className="text-[10px] font-mono uppercase text-slate-400">Commodity</span>
            <div className="text-sm font-bold font-mono text-white mt-0.5">{commodity}</div>
            <span className="text-[10px] font-mono text-slate-500">HS4 Code: {hs4}</span>
          </div>

          <div className="p-3 rounded bg-slate-950/60 border border-slate-800/80">
            <span className="text-[10px] font-mono uppercase text-slate-400">Partner Country</span>
            <div className="text-sm font-bold font-mono text-white mt-0.5">{country}</div>
            <span className="text-[10px] font-mono text-cyan-400">{tradeFlowDesc}</span>
          </div>

          <div className="p-3 rounded bg-slate-950/60 border border-slate-800/80">
            <span className="text-[10px] font-mono uppercase text-slate-400">Trade Flow Type</span>
            <div className="text-sm font-bold font-mono text-amber-300 mt-0.5">{tradeType}</div>
            <span className="text-[10px] font-mono text-slate-500">From India baseline</span>
          </div>

          <div className="p-3 rounded bg-slate-950/60 border border-slate-800/80">
            <span className="text-[10px] font-mono uppercase text-slate-400">Shock Multiplier</span>
            <div className="text-sm font-bold font-mono text-rose-400 mt-0.5">{shockIntensity}x</div>
            <span className="text-[10px] font-mono text-slate-500">Trade Share: {tradeShare}%</span>
          </div>
        </div>
      ) : (
        /* Edit Mode Form */
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6 p-4 rounded-lg bg-slate-950/80 border border-slate-800">
          <div>
            <label className="block text-[11px] font-mono text-slate-400 mb-1">Commodity</label>
            <input
              type="text"
              value={commodity}
              onChange={(e) => setCommodity(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-xs text-white font-mono focus:border-cyan-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-[11px] font-mono text-slate-400 mb-1">Partner Country</label>
            <input
              type="text"
              value={country}
              onChange={(e) => setCountry(e.target.value.toUpperCase())}
              className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-xs text-white font-mono focus:border-cyan-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-[11px] font-mono text-slate-400 mb-1">Trade Direction</label>
            <select
              value={tradeType}
              onChange={(e) => setTradeType(e.target.value as TradeFlow)}
              className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-xs text-white font-mono focus:border-cyan-500 focus:outline-none"
            >
              <option value="Export">Export (India → Partner)</option>
              <option value="Import">Import (Partner → India)</option>
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-mono text-slate-400 mb-1">Shock Intensity: {shockIntensity}x</label>
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
            <label className="block text-[11px] font-mono text-slate-400 mb-1">Trade Share: {tradeShare}%</label>
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

          <div>
            <label className="block text-[11px] font-mono text-slate-400 mb-1">HS4 Code</label>
            <input
              type="number"
              value={hs4}
              onChange={(e) => setHs4(parseInt(e.target.value))}
              className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-xs text-white font-mono focus:border-cyan-500 focus:outline-none"
            />
          </div>
        </div>
      )}

      {/* Footer Provenance and Action Buttons */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-4 border-t border-slate-800">
        <div className="flex items-center space-x-2">
          <ProvenanceTag tag="[LLM INFERENCE + GDELT DOC 2.0]" size="sm" />
          <span className="text-[11px] text-slate-500 font-mono">
            Effective Shock: {((shockIntensity * tradeShare) / 100).toFixed(4)}
          </span>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 rounded bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 text-xs font-mono transition-colors cursor-pointer"
          >
            Cancel / Clear
          </button>
          <button
            onClick={handleConfirm}
            className="px-5 py-2 rounded bg-gradient-to-r from-cyan-600 to-sky-600 hover:from-cyan-500 hover:to-sky-500 text-white font-mono text-xs font-bold shadow-glow-cyan flex items-center space-x-2 transition-all cursor-pointer"
          >
            <span>Confirm & Execute Cascade</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
