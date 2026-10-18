import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import {
  ShieldCheck,
  Clock,
  Layers,
  Sparkles,
  BookOpen,
  ArrowRight,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { Badge } from '../components/common/Badge';
import { ProvenanceTag } from '../components/common/ProvenanceTag';
import { DrishtiAnalysisResult, MitigationActionItem } from '../types/drishti';

interface OutletContextType {
  currentScenario: DrishtiAnalysisResult;
}

export const MitigationPage: React.FC = () => {
  const { currentScenario } = useOutletContext<OutletContextType>();
  const actions: MitigationActionItem[] = currentScenario?.mitigation_actions || [];
  const historicalAnalogs = currentScenario?.historical_context?.relevant_events || [];

  const [activeTab, setActiveTab] = useState<string>('ALL');

  const filteredActions = activeTab === 'ALL'
    ? actions
    : actions.filter(a => a.time_horizon.includes(activeTab));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center space-x-2 text-emerald-400 font-mono text-xs mb-1">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>POLICY & RESILIENCE ACTION PLAYBOOKS</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Targeted Mitigation Strategies & Policy Levers
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-3xl">
            Actionable playbooks synthesized by the Mitigation & Action Agent, structured across operational time horizons and grounded in historical precedents.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <Badge label="TIME-HORIZON STRUCTURED" variant="LOW" size="sm" />
          <Badge label="HISTORICALLY GROUNDED" variant="CYAN" size="sm" />
        </div>
      </div>

      {/* Time Horizon Filter Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-800/80 pb-3">
        {['ALL', 'Immediate', 'Short-Term', 'Medium-Term', 'Long-Term'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-mono font-medium transition-colors cursor-pointer ${
              activeTab === tab
                ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-700 shadow-glow-green'
                : 'bg-slate-900/60 text-slate-400 hover:text-slate-200 border border-slate-800'
            }`}
          >
            {tab === 'ALL' ? 'All Time Horizons' : tab}
          </button>
        ))}
      </div>

      {/* Action Playbook Cards List */}
      <div className="space-y-4">
        {filteredActions.map((act, idx) => (
          <div
            key={act.id || idx}
            className="card-terminal rounded-xl p-5 border border-slate-800 hover:border-slate-700 transition-colors space-y-3"
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
              <div className="flex items-center space-x-3">
                <span className="w-6 h-6 rounded-full bg-emerald-950 border border-emerald-700 text-emerald-300 font-mono text-xs flex items-center justify-center font-bold">
                  {idx + 1}
                </span>
                <h3 className="text-sm font-bold text-white font-mono">
                  {act.action}
                </h3>
              </div>

              <div className="flex items-center space-x-2">
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-300">
                  {act.time_horizon}
                </span>
                <Badge label={`Target: ${act.target_stakeholder}`} variant="CYAN" size="sm" />
              </div>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              <strong className="text-slate-200 font-semibold">Operational Rationale:</strong> {act.rationale}
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 text-xs font-mono">
              <div className="p-2.5 rounded bg-slate-950 border border-slate-800">
                <span className="text-[10px] uppercase text-slate-500 block mb-0.5">Policy Lever / Authority:</span>
                <span className="text-cyan-300 font-medium">{act.policy_lever}</span>
              </div>

              <div className="p-2.5 rounded bg-slate-950 border border-slate-800">
                <span className="text-[10px] uppercase text-slate-500 block mb-0.5">Expected Outcome:</span>
                <span className="text-emerald-300 font-medium">{act.expected_outcome || 'Stabilizes market channel within 45 days.'}</span>
              </div>
            </div>

            <div className="pt-2 flex items-center justify-between text-[11px] font-mono text-slate-500">
              <div className="flex items-center space-x-2">
                <span>Confidence: <strong className="text-slate-300">{act.confidence}</strong></span>
                <span>•</span>
                <span>Provenance:</span>
                <ProvenanceTag tag={act.provenance} size="sm" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Historical Analogs & Lessons Learned Section */}
      <div className="card-terminal rounded-xl p-5 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2 text-xs font-mono font-bold text-white">
            <BookOpen className="w-4 h-4 text-cyan-400" />
            <span>HISTORICAL EVENT ANALOGS & RELEVANCE PRECEDENTS</span>
          </div>
          <ProvenanceTag tag="[MCP HISTORICAL STORE]" size="sm" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {historicalAnalogs.map((event, idx) => (
            <div key={idx} className="p-4 rounded-lg bg-slate-950/80 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="font-bold text-cyan-300">{event.event}</span>
                <span className="text-slate-500">{event.year}</span>
              </div>
              <div className="text-[11px] font-mono text-purple-300">
                {event.similarity}
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                {event.lesson}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
