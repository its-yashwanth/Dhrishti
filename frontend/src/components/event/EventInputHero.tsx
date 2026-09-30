import React, { useState } from 'react';
import { Sparkles, ArrowRight, CornerDownLeft, Globe, Compass } from 'lucide-react';
import { PRESET_SCENARIOS } from '../../services/mockData';

interface EventInputHeroProps {
  onAnalyze: (query: string) => void;
  isLoading?: boolean;
}

export const EventInputHero: React.FC<EventInputHeroProps> = ({ onAnalyze, isLoading = false }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isLoading) return;
    onAnalyze(query.trim());
  };

  const handlePresetSelect = (presetQuery: string) => {
    setQuery(presetQuery);
    onAnalyze(presetQuery);
  };

  return (
    <div className="card-terminal rounded-xl p-6 border border-slate-800 relative overflow-hidden">
      {/* Background ambient glow */}
      <div className="absolute -top-24 -right-24 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-24 -left-24 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
        <div>
          <div className="flex items-center space-x-2 text-cyan-400 text-xs font-mono font-medium mb-1">
            <Compass className="w-4 h-4 animate-spin-slow" />
            <span>GEOPOLITICAL EVENT INGESTION</span>
          </div>
          <h2 className="text-xl font-bold text-white tracking-tight">
            What geopolitical event is being analyzed?
          </h2>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">
            Enter a natural-language description of an agricultural trade restriction, embargo, or corridor disruption.
            The Event Intelligence Agent will cross-reference GDELT and resolve structured shock parameters.
          </p>
        </div>

        <div className="flex items-center space-x-2 shrink-0">
          <span className="text-[11px] font-mono text-slate-400">Baseline perspective:</span>
          <span className="text-xs font-mono px-2 py-0.5 rounded bg-cyan-950 border border-cyan-800 text-cyan-300 font-semibold flex items-center space-x-1">
            <Globe className="w-3 h-3" />
            <span>INDIA</span>
          </span>
        </div>
      </div>

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="relative z-10 space-y-3">
        <div className="relative flex items-center">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
            placeholder="e.g. Russia stopped importing wheat from India amid sanitary disputes and Black Sea freight risks..."
            rows={2}
            className="w-full bg-[#070b14]/90 border border-slate-700/80 rounded-lg px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/50 resize-none font-sans leading-relaxed"
          />
          <button
            type="submit"
            disabled={!query.trim() || isLoading}
            className="absolute right-3 bottom-3 px-4 py-2 bg-gradient-to-r from-cyan-600 to-sky-600 hover:from-cyan-500 hover:to-sky-500 text-white rounded-md text-xs font-mono font-semibold flex items-center space-x-2 shadow-glow-cyan transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            {isLoading ? (
              <>
                <Sparkles className="w-3.5 h-3.5 animate-spin" />
                <span>Extracting...</span>
              </>
            ) : (
              <>
                <span>Analyze Shock</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </div>

        {/* Preset Chips */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <span className="text-[11px] font-mono text-slate-500 flex items-center space-x-1">
            <CornerDownLeft className="w-3 h-3 text-slate-600" />
            <span>Quick Presets:</span>
          </span>
          {PRESET_SCENARIOS.map((preset, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handlePresetSelect(preset.query)}
              className="text-xs px-2.5 py-1 rounded bg-slate-900/90 border border-slate-800 hover:border-cyan-700/80 hover:bg-slate-800/80 text-slate-300 hover:text-cyan-200 transition-colors flex items-center space-x-1.5 cursor-pointer"
            >
              <span className="text-[10px] font-mono px-1 rounded bg-slate-800 text-slate-400 font-medium">
                {preset.commodity}
              </span>
              <span>{preset.title}</span>
            </button>
          ))}
        </div>
      </form>
    </div>
  );
};
