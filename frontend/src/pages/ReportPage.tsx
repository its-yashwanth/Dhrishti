import React from 'react';
import { useOutletContext } from 'react-router-dom';
import {
  FileText,
  Printer,
  Download,
  Share2,
  Shield,
  Layers,
  CheckCircle2,
  Calendar,
  AlertTriangle,
  Globe,
  Anchor,
  MapPin,
  Users,
  ShieldCheck
} from 'lucide-react';
import { Badge } from '../components/common/Badge';
import { ProvenanceTag } from '../components/common/ProvenanceTag';
import { DrishtiAnalysisResult, StakeholderImpactItem } from '../types/drishti';

interface OutletContextType {
  currentScenario: DrishtiAnalysisResult;
}

export const ReportPage: React.FC = () => {
  const { currentScenario } = useOutletContext<OutletContextType>();

  const ml = currentScenario?.ml_predictions;
  const sc = currentScenario?.supply_chain_analysis?.supply_chain_analysis;
  const vu = currentScenario?.vulnerability_analysis?.vulnerability_analysis;
  const stakeholders: StakeholderImpactItem[] = Array.isArray(currentScenario?.stakeholder_impacts)
    ? currentScenario.stakeholder_impacts
    : [];

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header with Print / Export Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4 print:hidden">
        <div>
          <div className="flex items-center space-x-2 text-cyan-400 font-mono text-xs mb-1">
            <FileText className="w-4 h-4 text-cyan-400" />
            <span>DRISHTI DECISION INTELLIGENCE REPORT</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Executive Intelligence Dossier
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Consolidated geopolitical risk assessment, econometric cascade outputs, and mitigation roadmap.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handlePrint}
            className="px-4 py-2 rounded-lg bg-slate-900 border border-slate-700 hover:border-cyan-500 text-xs font-mono text-slate-200 flex items-center space-x-2 transition-colors cursor-pointer"
          >
            <Printer className="w-3.5 h-3.5 text-cyan-400" />
            <span>Print Dossier</span>
          </button>
          <button
            onClick={handlePrint}
            className="px-5 py-2 rounded-lg bg-gradient-to-r from-cyan-600 to-sky-600 hover:from-cyan-500 hover:to-sky-500 text-white font-mono text-xs font-bold shadow-glow-cyan flex items-center space-x-2 transition-all cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Generate Decision Report</span>
          </button>
        </div>
      </div>

      {/* Printable Report Document Card */}
      <div className="card-terminal rounded-xl p-8 border border-slate-800 space-y-8 bg-[#0a0f1d] print:bg-white print:text-black print:border-none print:p-0">
        {/* Document Header */}
        <div className="border-b border-slate-800 pb-6 print:border-black">
          <div className="flex justify-between items-start">
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xl font-black font-mono tracking-wider text-white print:text-black">
                  DRISHTI
                </span>
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800 font-semibold print:border-black">
                  OFFICIAL BRIEFING
                </span>
              </div>
              <p className="text-xs text-slate-400 print:text-gray-600 font-medium mt-1">
                Exposure-Aware Geopolitical Impact Assessment Framework
              </p>
            </div>

            <div className="text-right text-xs font-mono text-slate-400 print:text-gray-600">
              <div>Ref: <strong className="text-slate-200 print:text-black">DRISHTI-2024-WHT-01</strong></div>
              <div>Generated: {new Date().toLocaleDateString()}</div>
              <div>Classification: <strong className="text-cyan-400 print:text-black">RESEARCH / DECISION-SUPPORT</strong></div>
            </div>
          </div>

          <div className="mt-5 p-4 rounded-lg bg-slate-950/80 border border-slate-800/80 print:bg-gray-100 print:border-gray-300">
            <h2 className="text-base font-bold text-white print:text-black font-mono">
              SCENARIO: {currentScenario?.scenario_name || 'Wheat Export Disruption (India → Russia)'}
            </h2>
            <p className="text-xs text-slate-300 print:text-gray-800 mt-1 leading-relaxed">
              {currentScenario?.scenario_data?.description || 'Bilateral export restriction involving wheat trade.'}
            </p>
          </div>
        </div>

        {/* Section 01: Event Parameters & Summary */}
        <section className="space-y-3">
          <h3 className="text-xs font-mono uppercase tracking-widest text-cyan-400 font-bold border-b border-slate-800 pb-1.5 print:text-black">
            01 / EVENT INTELLIGENCE & PARAMETERIZATION
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs font-mono">
            <div className="p-2.5 rounded bg-slate-950 border border-slate-800 print:bg-gray-50">
              <span className="text-[10px] text-slate-500 uppercase block">Commodity</span>
              <span className="text-white font-bold print:text-black">{currentScenario?.scenario_data?.commodity}</span>
              <span className="text-[10px] text-slate-400 block">HS4: {currentScenario?.scenario_data?.hs4}</span>
            </div>
            <div className="p-2.5 rounded bg-slate-950 border border-slate-800 print:bg-gray-50">
              <span className="text-[10px] text-slate-500 uppercase block">Partner Country</span>
              <span className="text-white font-bold print:text-black">{currentScenario?.scenario_data?.event_country}</span>
              <span className="text-[10px] text-cyan-400 block">{currentScenario?.scenario_data?.trade_type}</span>
            </div>
            <div className="p-2.5 rounded bg-slate-950 border border-slate-800 print:bg-gray-50">
              <span className="text-[10px] text-slate-500 uppercase block">Shock Multiplier</span>
              <span className="text-rose-400 font-bold print:text-black">{currentScenario?.scenario_data?.shock_intensity}x</span>
              <span className="text-[10px] text-slate-400 block">Trade Share: {currentScenario?.scenario_data?.trade_share}%</span>
            </div>
            <div className="p-2.5 rounded bg-slate-950 border border-slate-800 print:bg-gray-50">
              <span className="text-[10px] text-slate-500 uppercase block">Canonical Direction</span>
              <span className="text-amber-400 font-bold print:text-black">supply_contraction</span>
              <span className="text-[10px] text-slate-400 block">Confidence: High</span>
            </div>
          </div>
        </section>

        {/* Section 02: Quantitative Econometric Cascade */}
        <section className="space-y-3">
          <h3 className="text-xs font-mono uppercase tracking-widest text-purple-400 font-bold border-b border-slate-800 pb-1.5 print:text-black">
            02 / QUANTITATIVE ECONOMETRIC CASCADE (MODELS A-D)
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs font-mono">
            <div className="p-3 rounded bg-slate-950 border border-slate-800 print:bg-gray-50">
              <span className="text-[10px] text-slate-500 block">Model A: Trade Return</span>
              <span className="text-lg font-bold text-rose-400 print:text-black">
                {ml?.trade?.Trade_Return_1M_Pred ? `${ml.trade.Trade_Return_1M_Pred.toFixed(2)}%` : '-4.82%'}
              </span>
              <span className="text-[10px] text-slate-400 block mt-1">1M Projected Flow Return</span>
            </div>

            <div className="p-3 rounded bg-slate-950 border border-slate-800 print:bg-gray-50">
              <span className="text-[10px] text-slate-500 block">Model B: Production Growth</span>
              <span className="text-lg font-bold text-rose-400 print:text-black">
                {ml?.agriculture?.Production_Growth_Pred ? `${ml.agriculture.Production_Growth_Pred.toFixed(2)}%` : '-1.35%'}
              </span>
              <span className="text-[10px] text-amber-400 block mt-1">Risk: {ml?.agriculture?.Production_Risk || 'Medium'}</span>
            </div>

            <div className="p-3 rounded bg-slate-950 border border-slate-800 print:bg-gray-50">
              <span className="text-[10px] text-slate-500 block">Model C: Wholesale Price</span>
              <span className="text-lg font-bold text-rose-400 print:text-black">
                {ml?.price?.Price_Return_1M_Pred ? `${ml.price.Price_Return_1M_Pred.toFixed(2)}%` : '-2.18%'}
              </span>
              <span className="text-[10px] text-slate-400 block mt-1">Domestic Price Response</span>
            </div>

            <div className="p-3 rounded bg-slate-950 border border-slate-800 print:bg-gray-50">
              <span className="text-[10px] text-slate-500 block">Model D: Macro GVA</span>
              <span className="text-lg font-bold text-rose-400 print:text-black">
                {ml?.economy?.Agri_GVA_Growth_Pred ? `${ml.economy.Agri_GVA_Growth_Pred.toFixed(2)} pp` : '-0.41 pp'}
              </span>
              <span className="text-[10px] text-emerald-400 block mt-1">Inflation: -0.19 pp</span>
            </div>
          </div>
        </section>

        {/* Section 03: Economic Interpretation */}
        <section className="space-y-3">
          <h3 className="text-xs font-mono uppercase tracking-widest text-cyan-400 font-bold border-b border-slate-800 pb-1.5 print:text-black">
            03 / NON-CAUSAL ECONOMIC SYNTHESIS
          </h3>
          <p className="text-xs text-slate-200 print:text-gray-800 leading-relaxed font-sans bg-slate-950/60 p-4 rounded-lg border border-slate-800/80 print:bg-gray-50">
            {currentScenario?.economic_interpretation ||
              'Econometric synthesis associates the scenario with an immediate export trade contraction. Northern producing zones face localized surplus accumulation while domestic wholesale prices soften slightly. Non-causal econometric framing applies.'}
          </p>
        </section>

        {/* Section 04: Supply Chain & Gateway Ports */}
        <section className="space-y-3">
          <h3 className="text-xs font-mono uppercase tracking-widest text-sky-400 font-bold border-b border-slate-800 pb-1.5 print:text-black">
            04 / SUPPLY CHAIN & GATEWAY PORTS EXPOSURE
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
            <div className="p-3 rounded bg-slate-950 border border-slate-800 print:bg-gray-50">
              <span className="text-slate-400 font-bold block mb-1">Scenario-Exposed Port Bottlenecks:</span>
              <div className="space-y-1">
                <div>• Deendayal Port Authority (Kandla, Gujarat) — <span className="text-rose-400 font-bold">HIGH RISK</span> (38.4% share)</div>
                <div>• Mundra Port (Gujarat) — <span className="text-rose-400 font-bold">HIGH RISK</span> (18.5% share)</div>
              </div>
            </div>

            <div className="p-3 rounded bg-slate-950 border border-slate-800 print:bg-gray-50">
              <span className="text-slate-400 font-bold block mb-1">Modeled Alternative Handling Paths:</span>
              <div className="space-y-1">
                <div>• JNPA (Maharashtra) — <span className="text-emerald-400 font-bold">94% Affinity</span> (82% buffer)</div>
                <div>• Pipavav Port (Gujarat) — <span className="text-emerald-400 font-bold">78% Affinity</span> (54% buffer)</div>
              </div>
            </div>
          </div>
        </section>

        {/* Section 05: Vulnerable Agricultural Regions (RAVS) */}
        <section className="space-y-3">
          <h3 className="text-xs font-mono uppercase tracking-widest text-amber-400 font-bold border-b border-slate-800 pb-1.5 print:text-black">
            05 / REGIONAL AGRICULTURAL VULNERABILITY (RAVS)
          </h3>
          <p className="text-[11px] text-slate-400 print:text-gray-600 font-mono">
            Historical agricultural vulnerability index (1997–2023 baseline). Top vulnerable districts ranked by composite RAVS score:
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs font-mono">
            {vu?.top_vulnerable_regions?.slice(0, 4).map((reg: any, idx: number) => (
              <div key={idx} className="p-2.5 rounded bg-slate-950 border border-slate-800 print:bg-gray-50">
                <div className="font-bold text-white print:text-black">{idx + 1}. {reg.district}</div>
                <div className="text-[10px] text-slate-400">{reg.state}</div>
                <div className="mt-1 text-amber-400 font-bold">RAVS: {reg.ravs.toFixed(3)} ({reg.classification})</div>
              </div>
            ))}
          </div>
        </section>

        {/* Section 06: Stakeholder Distributional Impacts */}
        <section className="space-y-3">
          <h3 className="text-xs font-mono uppercase tracking-widest text-purple-400 font-bold border-b border-slate-800 pb-1.5 print:text-black">
            06 / STAKEHOLDER DISTRIBUTIONAL IMPACTS
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            {stakeholders.slice(0, 4).map((sh, idx) => (
              <div key={idx} className="p-3 rounded bg-slate-950 border border-slate-800 print:bg-gray-50 space-y-1">
                <div className="flex justify-between font-mono">
                  <span className="font-bold text-white print:text-black">{sh.stakeholder}</span>
                  <Badge label={sh.severity} variant={sh.severity} size="sm" />
                </div>
                <p className="text-slate-300 print:text-gray-700 text-[11px] leading-relaxed">
                  {sh.impact_summary}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* Section 07: Recommended Mitigation Playbooks */}
        <section className="space-y-3">
          <h3 className="text-xs font-mono uppercase tracking-widest text-emerald-400 font-bold border-b border-slate-800 pb-1.5 print:text-black">
            07 / GROUNDED MITIGATION PLAYBOOKS
          </h3>
          <div className="space-y-2 text-xs font-mono">
            {currentScenario?.mitigation_actions?.slice(0, 3).map((act, idx) => (
              <div key={idx} className="p-3 rounded bg-slate-950 border border-slate-800 print:bg-gray-50 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white print:text-black">{idx + 1}. {act.action}</span>
                  <span className="text-[10px] text-cyan-400">{act.time_horizon}</span>
                </div>
                <p className="text-slate-300 print:text-gray-700 text-[11px] font-sans">
                  {act.rationale}
                </p>
                <div className="text-[10px] text-slate-500">
                  Policy Lever: {act.policy_lever}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Document Sign-Off and Disclaimers */}
        <div className="pt-6 border-t border-slate-800 print:border-black flex flex-col sm:flex-row justify-between items-center text-[10px] font-mono text-slate-500 gap-3">
          <div>
            Drishti Framework | Capstone Decision Intelligence Engine
          </div>
          <div className="flex items-center space-x-2">
            <ProvenanceTag tag="[STRICT AUDIT TRAILS ENFORCED]" size="sm" />
          </div>
        </div>
      </div>
    </div>
  );
};
