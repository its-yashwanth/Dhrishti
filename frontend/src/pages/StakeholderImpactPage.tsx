import React from 'react';
import { useOutletContext } from 'react-router-dom';
import {
  Users,
  Wheat,
  ShoppingBag,
  TrendingDown,
  TrendingUp,
  Globe,
  Building2,
  Landmark,
  ArrowRight,
  ShieldAlert,
  Layers,
  Sparkles
} from 'lucide-react';
import { Badge } from '../components/common/Badge';
import { ProvenanceTag } from '../components/common/ProvenanceTag';
import { DrishtiAnalysisResult, StakeholderImpactItem } from '../types/drishti';

interface OutletContextType {
  currentScenario: DrishtiAnalysisResult;
}

export const StakeholderImpactPage: React.FC = () => {
  const { currentScenario } = useOutletContext<OutletContextType>();
  const stakeholders: StakeholderImpactItem[] = Array.isArray(currentScenario?.stakeholder_impacts)
    ? currentScenario.stakeholder_impacts
    : [];

  const getStakeholderIcon = (name: string) => {
    const n = name.toLowerCase();
    if (n.includes('farmer')) return <Wheat className="w-5 h-5 text-amber-400" />;
    if (n.includes('consumer')) return <ShoppingBag className="w-5 h-5 text-cyan-400" />;
    if (n.includes('exporter') || n.includes('trader')) return <TrendingDown className="w-5 h-5 text-rose-400" />;
    if (n.includes('importer')) return <Globe className="w-5 h-5 text-sky-400" />;
    if (n.includes('region')) return <Building2 className="w-5 h-5 text-purple-400" />;
    return <Landmark className="w-5 h-5 text-emerald-400" />;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center space-x-2 text-purple-400 font-mono text-xs mb-1">
            <Users className="w-4 h-4 text-purple-400" />
            <span>DISTRIBUTIONAL IMPACT ENGINE</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Multi-Stakeholder Economic Disaggregation
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-3xl">
            Deterministic mapping of asymmetrical shock exposure across primary producers, international exporters, domestic consumers, and government balances.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <Badge label="DETERMINISTIC STAKEHOLDER RULES" variant="PURPLE" size="sm" />
          <Badge label="6 KEY ACTOR GROUPS" variant="CYAN" size="sm" />
        </div>
      </div>

      {/* Grid of Stakeholder Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {stakeholders.map((sh, idx) => (
          <div
            key={idx}
            className="card-terminal rounded-xl p-5 border border-slate-800 flex flex-col justify-between hover:border-slate-700 transition-colors"
          >
            <div>
              {/* Card Header */}
              <div className="flex items-center justify-between mb-3 border-b border-slate-800/80 pb-3">
                <div className="flex items-center space-x-3">
                  <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                    {getStakeholderIcon(sh.stakeholder)}
                  </div>
                  <div>
                    <h3 className="text-sm font-bold font-mono text-white">
                      {sh.stakeholder}
                    </h3>
                    <p className="text-[10px] text-slate-400 font-sans">{sh.role}</p>
                  </div>
                </div>

                <Badge label={sh.severity} variant={sh.severity} size="sm" />
              </div>

              {/* Core Impact Narrative */}
              <p className="text-xs text-slate-200 font-medium leading-relaxed mb-3">
                {sh.impact_summary}
              </p>

              {/* Detailed Rationale */}
              <p className="text-[11px] text-slate-400 leading-relaxed mb-4">
                {sh.detailed_rationale}
              </p>

              {/* Transmission Channels */}
              {sh.transmission_channels && sh.transmission_channels.length > 0 && (
                <div className="mb-4 space-y-1.5">
                  <span className="text-[10px] font-mono uppercase text-slate-500 font-bold block">
                    Transmission Channels:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {sh.transmission_channels.map((ch, cIdx) => (
                      <span
                        key={cIdx}
                        className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-slate-300"
                      >
                        {ch}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Footer with Evidence and Provenance */}
            <div className="pt-3 border-t border-slate-800/80 flex flex-col space-y-2">
              <div className="flex items-center justify-between text-[10px]">
                <span className="text-slate-500 font-mono">Grounded Signal:</span>
                <ProvenanceTag tag={sh.provenance || '[STAKEHOLDER ENGINE]'} size="sm" />
              </div>

              {sh.evidence_sources && (
                <div className="text-[9px] font-mono text-slate-500 truncate">
                  Evidence: {sh.evidence_sources.join(', ')}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
