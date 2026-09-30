import React, { useState } from 'react';
import { useNavigate, useOutletContext } from 'react-router-dom';
import { EventInputHero } from '../components/event/EventInputHero';
import { ScenarioReviewModal } from '../components/event/ScenarioReviewModal';
import { ProcessingPipeline } from '../components/event/ProcessingPipeline';
import { KpiCard } from '../components/common/KpiCard';
import { Badge } from '../components/common/Badge';
import { ProvenanceTag } from '../components/common/ProvenanceTag';
import { DrishtiAPI, PipelineStageEvent } from '../services/api';
import { DrishtiAnalysisResult, StructuredEvent, TradeFlow } from '../types/drishti';
import {
  Sparkles,
  ArrowRight,
  TrendingDown,
  Globe2,
  MapPin,
  Users,
  ShieldCheck,
  FileText,
  AlertTriangle,
  Info
} from 'lucide-react';

interface OutletContextType {
  currentScenario: DrishtiAnalysisResult;
  refreshScenario: () => void;
}

export const DashboardPage: React.FC = () => {
  const { currentScenario, refreshScenario } = useOutletContext<OutletContextType>();
  const navigate = useNavigate();

  const [extractedEvent, setExtractedEvent] = useState<StructuredEvent | null>(null);
  const [isExtracting, setIsExtracting] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const [currentStage, setCurrentStage] = useState<PipelineStageEvent['stage']>();
  const [stagesStatus, setStagesStatus] = useState<Record<string, 'pending' | 'active' | 'completed' | 'error'>>({});

  // Trigger natural language extraction
  const handleAnalyzeQuery = async (query: string) => {
    setIsExtracting(true);
    try {
      const extracted = await DrishtiAPI.extractEvent(query);
      setExtractedEvent(extracted);
    } catch {
      // Ignore
    } finally {
      setIsExtracting(false);
    }
  };

  // Execute full cascade after review
  const handleConfirmScenario = async (params: {
    commodity: string;
    partner_country: string;
    trade_type: TradeFlow;
    shock_intensity: number;
    trade_share: number;
    hs4: number;
  }) => {
    setExtractedEvent(null);
    setIsExecuting(true);
    setStagesStatus({});

    try {
      await DrishtiAPI.runFullAnalysis(
        {
          query: extractedEvent?.summary || 'Geopolitical trade shock',
          ...params
        },
        (progress) => {
          setCurrentStage(progress.stage);
          setStagesStatus(prev => ({
            ...prev,
            [progress.stage]: progress.status
          }));
        }
      );
      refreshScenario();
    } catch {
      // Error handling
    } finally {
      setIsExecuting(false);
    }
  };

  const scData = currentScenario?.supply_chain_analysis?.supply_chain_analysis;
  const vuData = currentScenario?.vulnerability_analysis?.vulnerability_analysis;
  const mlPreds = currentScenario?.ml_predictions;

  return (
    <div className="space-y-6">
      {/* 1. Large Natural Language Input Hero */}
      <EventInputHero onAnalyze={handleAnalyzeQuery} isLoading={isExtracting} />

      {/* 2. Scenario Review Confirmation Panel */}
      {extractedEvent && (
        <ScenarioReviewModal
          event={extractedEvent}
          onConfirm={handleConfirmScenario}
          onCancel={() => setExtractedEvent(null)}
        />
      )}

      {/* 3. Real-time Pipeline Execution Bar */}
      {(isExecuting || Object.keys(stagesStatus).length > 0) && (
        <ProcessingPipeline
          currentStage={currentStage}
          stagesStatus={stagesStatus}
        />
      )}

      {/* 4. Active Scenario Executive Banner */}
      <div className="card-terminal rounded-xl p-5 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-cyan-400 mb-1">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
            <span>ACTIVE DECISION CONTEXT</span>
            <span className="text-slate-600">|</span>
            <span className="text-slate-400">HS4: {currentScenario?.scenario_data?.hs4 || 1001}</span>
          </div>
          <h2 className="text-lg font-bold text-white tracking-tight flex items-center space-x-2">
            <span>{currentScenario?.scenario_name || 'Wheat Export Disruption (India → Russia)'}</span>
            <Badge
              label={currentScenario?.scenario_data?.trade_type || 'Export'}
              variant="PURPLE"
              size="sm"
            />
          </h2>
          <p className="text-xs text-slate-300 mt-1 max-w-3xl leading-relaxed">
            {currentScenario?.scenario_data?.description ||
              'Bilateral export restriction on Indian wheat with 1.5x shock intensity across 5.0% trade share baseline.'}
          </p>
        </div>

        <div className="flex items-center space-x-3 shrink-0">
          <button
            onClick={() => navigate('/event-analysis')}
            className="px-3.5 py-1.5 rounded bg-slate-900 border border-slate-700 hover:border-cyan-600 text-xs font-mono text-slate-300 hover:text-white transition-colors cursor-pointer"
          >
            Adjust Parameters
          </button>
          <button
            onClick={() => navigate('/report')}
            className="px-4 py-1.5 rounded bg-gradient-to-r from-cyan-600 to-sky-600 hover:from-cyan-500 hover:to-sky-500 text-white font-mono text-xs font-semibold shadow-glow-cyan flex items-center space-x-1.5 transition-all cursor-pointer"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>View Full Report</span>
          </button>
        </div>
      </div>

      {/* 5. Summary KPI Cards (6 Critical Intelligence Vectors) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3">
        {/* Trade Impact (Model A) */}
        <KpiCard
          title="Trade Flow Return"
          value={mlPreds?.trade?.Trade_Return_1M_Pred ? `${mlPreds.trade.Trade_Return_1M_Pred > 0 ? '+' : ''}${mlPreds.trade.Trade_Return_1M_Pred.toFixed(2)}%` : 'N/A'}
          direction={mlPreds?.trade?.Trade_Return_1M_Pred && mlPreds.trade.Trade_Return_1M_Pred < 0 ? 'down' : 'up'}
          severity="HIGH"
          modelBadge="Model A"
          subtitle="Projected 1-Month Trade Return"
          provenance="[ML INFERENCE]"
          accentColor="purple"
        />

        {/* Agricultural Production (Model B) */}
        <KpiCard
          title="National Production"
          value={mlPreds?.agriculture?.Production_Growth_Pred ? `${mlPreds.agriculture.Production_Growth_Pred > 0 ? '+' : ''}${mlPreds.agriculture.Production_Growth_Pred.toFixed(2)}%` : 'N/A'}
          direction={mlPreds?.agriculture?.Production_Growth_Pred && mlPreds.agriculture.Production_Growth_Pred < 0 ? 'down' : 'up'}
          severity={mlPreds?.agriculture?.Production_Risk === 'High' ? 'HIGH' : 'MODERATE'}
          modelBadge="Model B"
          subtitle={`National Growth | Risk: ${mlPreds?.agriculture?.Production_Risk || 'Medium'}`}
          provenance="[ML INFERENCE]"
          accentColor="purple"
        />

        {/* Price Impact (Model C) */}
        <KpiCard
          title="Wholesale Price"
          value={mlPreds?.price?.Price_Return_1M_Pred ? `${mlPreds.price.Price_Return_1M_Pred > 0 ? '+' : ''}${mlPreds.price.Price_Return_1M_Pred.toFixed(2)}%` : 'N/A'}
          direction={mlPreds?.price?.Price_Return_1M_Pred && mlPreds.price.Price_Return_1M_Pred < 0 ? 'down' : 'up'}
          severity="MODERATE"
          modelBadge="Model C"
          subtitle="Domestic Wholesale Deflection"
          provenance="[ML INFERENCE]"
          accentColor="purple"
        />

        {/* Economic GVA (Model D) */}
        <KpiCard
          title="Agri GVA Growth"
          value={mlPreds?.economy?.Agri_GVA_Growth_Pred ? `${mlPreds.economy.Agri_GVA_Growth_Pred > 0 ? '+' : ''}${mlPreds.economy.Agri_GVA_Growth_Pred.toFixed(2)} pp` : 'N/A'}
          direction={mlPreds?.economy?.Agri_GVA_Growth_Pred && mlPreds.economy.Agri_GVA_Growth_Pred < 0 ? 'down' : 'neutral'}
          severity="LOW"
          modelBadge="Model D"
          subtitle={`Food Inflation: ${mlPreds?.economy?.Inflation_Change_Pred ? `${mlPreds.economy.Inflation_Change_Pred.toFixed(2)} pp` : 'N/A'}`}
          provenance="[ML INFERENCE]"
          accentColor="purple"
        />

        {/* Regional Vulnerability (RAVS) */}
        <KpiCard
          title="Peak Vulnerability"
          value={vuData?.regional_scores_summary?.max_ravs?.toFixed(3) || '0.841'}
          severity="HIGH"
          modelBadge="RAVS Index"
          subtitle={`Mean RAVS: ${vuData?.regional_scores_summary?.mean_ravs?.toFixed(3) || '0.412'} (320 Dists)`}
          provenance="[AGRICULTURE DATA]"
          accentColor="amber"
          footerNote="Top: Firozpur, PB"
        />

        {/* Supply Chain Exposure */}
        <KpiCard
          title="Effective Shock"
          value={scData?.scenario_exposure?.effective_shock?.toFixed(4) || '0.0750'}
          severity="HIGH"
          modelBadge="Graph Engine"
          subtitle={`Bottlenecks: ${scData?.critical_ports?.length || 2} Ports Flagged`}
          provenance="[GRAPH-DERIVED]"
          accentColor="cyan"
          footerNote="Kandla / JNPA"
        />
      </div>

      {/* 6. Non-Causal Econometric Interpretation Panel */}
      <div className="card-terminal rounded-xl p-5 border border-slate-800">
        <div className="flex items-center justify-between mb-3 border-b border-slate-800 pb-2.5">
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-purple-400" />
            <h3 className="text-xs font-mono uppercase tracking-widest text-slate-300 font-semibold">
              NON-CAUSAL ECONOMETRIC INTERPRETATION
            </h3>
          </div>
          <ProvenanceTag tag="[LLM SYNTHESIS OF QUANTITATIVE FORECASTS]" size="sm" />
        </div>

        <p className="text-xs text-slate-200 leading-relaxed font-sans">
          {currentScenario?.economic_interpretation ||
            'Econometric forecasts associate the scenario with an immediate export volume contraction, generating localized surplus accumulation in northern primary mandis. Supply chain network exposure highlights Deendayal Port Authority as the primary gateway bottleneck.'}
        </p>

        <div className="mt-3 pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
          <span className="flex items-center space-x-1.5 text-slate-400 font-mono">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
            <span>Strict non-causal disclaimer: Model forecasts represent statistical correlations, not deterministic proof.</span>
          </span>
          <span className="font-mono text-purple-400">
            {currentScenario?.llm_usage?.economic_interpretation || 'Gemini 2.5 Flash'}
          </span>
        </div>
      </div>

      {/* 7. Deep-Dive Domain Navigation Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Supply Chain Card */}
        <div
          onClick={() => navigate('/supply-chain')}
          className="card-terminal rounded-xl p-5 border border-slate-800 hover:border-cyan-500/60 transition-all duration-200 cursor-pointer group flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="p-2.5 rounded-lg bg-cyan-950/80 border border-cyan-800 text-cyan-400 group-hover:scale-105 transition-transform">
                <Globe2 className="w-5 h-5" />
              </div>
              <Badge label="3D GLOBE" variant="CYAN" size="sm" />
            </div>
            <h3 className="text-sm font-bold text-white group-hover:text-cyan-300 transition-colors">
              Supply Chain & Gateway Ports
            </h3>
            <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
              Interactive 3D network globe tracking scenario-exposed connections and modeled alternative handling paths across major Indian ports.
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-cyan-400 font-mono font-medium">
            <span>Explore Port Network</span>
            <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
          </div>
        </div>

        {/* Vulnerability Card */}
        <div
          onClick={() => navigate('/vulnerability')}
          className="card-terminal rounded-xl p-5 border border-slate-800 hover:border-amber-500/60 transition-all duration-200 cursor-pointer group flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="p-2.5 rounded-lg bg-amber-950/80 border border-amber-800 text-amber-400 group-hover:scale-105 transition-transform">
                <MapPin className="w-5 h-5" />
              </div>
              <Badge label="RAVS MAP" variant="MODERATE" size="sm" />
            </div>
            <h3 className="text-sm font-bold text-white group-hover:text-amber-300 transition-colors">
              Regional Agricultural Vulnerability
            </h3>
            <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
              District-level spatial index (RAVS) across 320 producing zones capturing production share, yield variability, and crop concentration.
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-amber-400 font-mono font-medium">
            <span>Open India Map</span>
            <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
          </div>
        </div>

        {/* Stakeholder Card */}
        <div
          onClick={() => navigate('/stakeholders')}
          className="card-terminal rounded-xl p-5 border border-slate-800 hover:border-purple-500/60 transition-all duration-200 cursor-pointer group flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="p-2.5 rounded-lg bg-purple-950/80 border border-purple-800 text-purple-400 group-hover:scale-105 transition-transform">
                <Users className="w-5 h-5" />
              </div>
              <Badge label="6 GROUPS" variant="PURPLE" size="sm" />
            </div>
            <h3 className="text-sm font-bold text-white group-hover:text-purple-300 transition-colors">
              Distributional Stakeholder Impacts
            </h3>
            <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
              Deterministic impact disaggregation across Farmers, Exporters, Consumers, Foreign Importers, Regional Clusters, and Government.
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-purple-400 font-mono font-medium">
            <span>View Distribution</span>
            <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
          </div>
        </div>

        {/* Mitigation Card */}
        <div
          onClick={() => navigate('/mitigation')}
          className="card-terminal rounded-xl p-5 border border-slate-800 hover:border-emerald-500/60 transition-all duration-200 cursor-pointer group flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="p-2.5 rounded-lg bg-emerald-950/80 border border-emerald-800 text-emerald-400 group-hover:scale-105 transition-transform">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <Badge label="PLAYBOOK" variant="LOW" size="sm" />
            </div>
            <h3 className="text-sm font-bold text-white group-hover:text-emerald-300 transition-colors">
              Mitigation & Action Playbooks
            </h3>
            <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
              Time-horizon intervention playbooks (Immediate, Short-Term, Medium-Term, Long-Term) grounded in historical precedents.
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-emerald-400 font-mono font-medium">
            <span>Inspect Recommendations</span>
            <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
          </div>
        </div>
      </div>
    </div>
  );
};
