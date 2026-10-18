import React from 'react';
import {
  Network,
  Cpu,
  Shield,
  Layers,
  Sparkles,
  GitBranch,
  Database,
  ArrowRight,
  Terminal,
  Anchor,
  MapPin,
  Users
} from 'lucide-react';
import { Badge } from '../components/common/Badge';
import { ProvenanceTag } from '../components/common/ProvenanceTag';

export const ArchitecturePage: React.FC = () => {
  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-2 text-purple-400 font-mono text-xs mb-1">
          <Network className="w-4 h-4 text-purple-400" />
          <span>SYSTEM ARCHITECTURE & METHODOLOGY SPECIFICATION</span>
        </div>
        <h1 className="text-2xl font-bold text-white tracking-tight">
          Drishti Framework Architecture
        </h1>
        <p className="text-xs text-slate-400 mt-1 max-w-3xl">
          Complete structural breakdown of the quantitative econometric cascade, agent decision-support suite, and supply chain topological network.
        </p>
      </div>

      {/* System Flow Diagram */}
      <div className="card-terminal rounded-xl p-6 border border-slate-800 space-y-4">
        <h2 className="text-xs font-mono uppercase tracking-widest text-slate-300 font-semibold flex items-center space-x-2">
          <Layers className="w-4 h-4 text-cyan-400" />
          <span>END-TO-END EXECUTION CASCADE</span>
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-lg bg-slate-950 border border-cyan-800 space-y-2">
            <div className="text-[10px] font-mono text-cyan-400 font-bold uppercase">Layer 1: Ingestion</div>
            <div className="text-sm font-bold text-white font-mono">Event Intelligence Agent</div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Consumes natural-language queries, calls GDELT DOC 2.0 via MCP, resolves HS4 codes, and classifies canonical shock direction.
            </p>
            <ProvenanceTag tag="[GDELT DOC 2.0]" size="sm" />
          </div>

          <div className="p-4 rounded-lg bg-slate-950 border border-purple-800 space-y-2">
            <div className="text-[10px] font-mono text-purple-400 font-bold uppercase">Layer 2: Quantitative</div>
            <div className="text-sm font-bold text-white font-mono">Models A → B → C → D</div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Hierarchical econometric models calculating trade returns, national production growth, domestic price deflection, and macro GVA impacts.
            </p>
            <ProvenanceTag tag="[ML CASCADE]" size="sm" />
          </div>

          <div className="p-4 rounded-lg bg-slate-950 border border-sky-800 space-y-2">
            <div className="text-[10px] font-mono text-sky-400 font-bold uppercase">Layer 3: Network & Spatial</div>
            <div className="text-sm font-bold text-white font-mono">Supply Chain & RAVS Agents</div>
            <p className="text-xs text-slate-400 leading-relaxed">
              MultiDiGraph port bottleneck analysis, modeled alternative handling paths, and 320-district agricultural vulnerability scoring.
            </p>
            <ProvenanceTag tag="[GRAPH + DES DATA]" size="sm" />
          </div>

          <div className="p-4 rounded-lg bg-slate-950 border border-emerald-800 space-y-2">
            <div className="text-[10px] font-mono text-emerald-400 font-bold uppercase">Layer 4: Decision Support</div>
            <div className="text-sm font-bold text-white font-mono">Stakeholder & Mitigation</div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Deterministic rule scoring across 6 key stakeholder groups and time-horizon grounded policy resilience playbooks.
            </p>
            <ProvenanceTag tag="[DETERMINISTIC RULES]" size="sm" />
          </div>
        </div>
      </div>

      {/* Models A-D Specifications Grid */}
      <div className="card-terminal rounded-xl p-6 border border-slate-800 space-y-4">
        <h2 className="text-xs font-mono uppercase tracking-widest text-slate-300 font-semibold flex items-center space-x-2">
          <Cpu className="w-4 h-4 text-purple-400" />
          <span>QUANTITATIVE ML MODEL CHECKPOINTS</span>
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
          <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-1.5">
            <div className="flex justify-between items-center">
              <span className="font-bold text-purple-300">Model A: Trade Return Estimator</span>
              <Badge label="Trained & Verified" variant="PURPLE" size="sm" />
            </div>
            <div className="text-slate-400">Architecture: XGBoost + Random Forest Ensemble</div>
            <div className="text-slate-400">Target: 1-Month Forward Trade Return (%)</div>
            <div className="text-slate-400">Inputs: Goldstein score, Average tone, Lagged returns, Effective shock</div>
            <div className="text-emerald-400 font-bold">Performance: R² = 0.68 | MAE = 1.14%</div>
          </div>

          <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-1.5">
            <div className="flex justify-between items-center">
              <span className="font-bold text-purple-300">Model B: Agricultural Production</span>
              <Badge label="Trained & Verified" variant="PURPLE" size="sm" />
            </div>
            <div className="text-slate-400">Architecture: LightGBM Gradient Boosted Regressor</div>
            <div className="text-slate-400">Target: National Production Growth Deflection (%)</div>
            <div className="text-slate-400">Inputs: Trade signal transmission, multi-year crop momentum, area yield trends</div>
            <div className="text-emerald-400 font-bold">Outputs: Numerical growth prediction + Risk tier classification</div>
          </div>

          <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-1.5">
            <div className="flex justify-between items-center">
              <span className="font-bold text-purple-300">Model C: Domestic Wholesale Price</span>
              <Badge label="Trained & Verified" variant="PURPLE" size="sm" />
            </div>
            <div className="text-slate-400">Architecture: Multi-lag Ridge Vector Autoregressor (VAR)</div>
            <div className="text-slate-400">Target: Wholesale Price Index Return (%)</div>
            <div className="text-slate-400">Mechanism: Domestic supply re-absorption and mandi gate accumulation</div>
            <div className="text-cyan-400 font-bold">Status: Synchronized with Model A & B outputs</div>
          </div>

          <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-1.5">
            <div className="flex justify-between items-center">
              <span className="font-bold text-purple-300">Model D: Macroeconomic Transfer</span>
              <Badge label="Trained & Verified" variant="PURPLE" size="sm" />
            </div>
            <div className="text-slate-400">Architecture: Macroeconomic Elasticity Transfer Matrix</div>
            <div className="text-slate-400">Targets: Agri GVA Growth (pp), Food Inflation Delta (pp)</div>
            <div className="text-slate-400">Inputs: Sectoral harvest value deflections & retail transmission lags</div>
            <div className="text-cyan-400 font-bold">Status: Macroeconomic translation layer</div>
          </div>
        </div>
      </div>

      {/* Extensibility & Research Statement */}
      <div className="card-terminal rounded-xl p-6 border border-slate-800 space-y-3">
        <h2 className="text-xs font-mono uppercase tracking-widest text-slate-300 font-semibold flex items-center space-x-2">
          <Terminal className="w-4 h-4 text-emerald-400" />
          <span>RESEARCH EXTENSIBILITY & FUTURE WORK</span>
        </h2>
        <p className="text-xs text-slate-300 leading-relaxed">
          The Drishti presentation layer communicates strictly through standardized API interfaces (`services/api.ts`).
          Backend components—including retrieval-augmented generation (RAG), expanded MultiDiGraph datasets, satellite-derived NDVI integration, and multi-commodity trade baskets—can be upgraded independently without altering the presentation contract.
        </p>
        <div className="pt-2 flex flex-wrap gap-2 text-[10px] font-mono">
          <span className="px-2.5 py-1 rounded bg-slate-950 border border-slate-800 text-slate-300">
            Frontend: React 19 + TypeScript + Vite + Tailwind CSS
          </span>
          <span className="px-2.5 py-1 rounded bg-slate-950 border border-slate-800 text-slate-300">
            Backend: Python 3.11 + NetworkX + Scikit-Learn + LightGBM + FastAPI
          </span>
        </div>
      </div>
    </div>
  );
};
