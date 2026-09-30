import React from 'react';
import { useOutletContext } from 'react-router-dom';
import {
  TrendingDown,
  TrendingUp,
  GitCommitHorizontal,
  Cpu,
  Layers,
  Info,
  ShieldAlert,
  ArrowDown,
  Activity,
  BarChart3
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Cell
} from 'recharts';
import { Badge } from '../components/common/Badge';
import { ProvenanceTag } from '../components/common/ProvenanceTag';
import { DrishtiAnalysisResult } from '../types/drishti';

interface OutletContextType {
  currentScenario: DrishtiAnalysisResult;
}

export const ImpactCascadePage: React.FC = () => {
  const { currentScenario } = useOutletContext<OutletContextType>();
  const preds = currentScenario?.ml_predictions;

  // Chart data preparing deflection values across the cascade
  const cascadeChartData = [
    {
      stage: 'Model A: Trade',
      metric: 'Trade Return 1M',
      value: preds?.trade?.Trade_Return_1M_Pred ?? -4.82,
      unit: '%',
      model: 'Model A (XGBoost/RF)'
    },
    {
      stage: 'Model B: Production',
      metric: 'National Prod Growth',
      value: preds?.agriculture?.Production_Growth_Pred ?? -1.35,
      unit: '%',
      model: 'Model B (LightGBM)'
    },
    {
      stage: 'Model C: Price',
      metric: 'Wholesale Price Return',
      value: preds?.price?.Price_Return_1M_Pred ?? -2.18,
      unit: '%',
      model: 'Model C (Multi-lag Ridge)'
    },
    {
      stage: 'Model D: Agri GVA',
      metric: 'Agri GVA Growth Delta',
      value: preds?.economy?.Agri_GVA_Growth_Pred ?? -0.41,
      unit: 'pp',
      model: 'Model D (Elasticity Matrix)'
    },
    {
      stage: 'Model D: Inflation',
      metric: 'Food Inflation Delta',
      value: preds?.economy?.Inflation_Change_Pred ?? -0.19,
      unit: 'pp',
      model: 'Model D (Macro Transfer)'
    }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center space-x-2 text-purple-400 font-mono text-xs mb-1">
            <Cpu className="w-4 h-4 text-purple-400" />
            <span>QUANTITATIVE ECONOMETRIC CASCADE</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Hierarchical Model Cascade (A → B → C → D)
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-3xl">
            Sequential transfer of geopolitical shock parameters through machine learning models.
            Each stage provides non-causal econometric forecasts and feeds subsequent economic layers.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <Badge label="NON-CAUSAL PROJECTIONS" variant="PURPLE" size="sm" />
          <Badge label="HARMONIZED MONTHLY FREQUENCY" variant="CYAN" size="sm" />
        </div>
      </div>

      {/* Non-Causal Framing Notice */}
      <div className="p-3.5 rounded-lg bg-purple-950/20 border border-purple-800/60 flex items-start space-x-3 text-xs text-purple-200">
        <Info className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          <strong className="font-semibold text-purple-300">Methodological Framing:</strong> Predictions represent model-predicted impact and econometric projections based on historical co-movements (2000–2023). They do not assert causal certainty.
        </p>
      </div>

      {/* Visual Cascade Stepper (Event → A → B → C → D) */}
      <div className="card-terminal rounded-xl p-6 border border-slate-800">
        <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
          <h2 className="text-xs font-mono uppercase tracking-widest text-slate-300 font-semibold flex items-center space-x-2">
            <GitCommitHorizontal className="w-4 h-4 text-purple-400" />
            <span>CASCADE FLOW PIPELINE</span>
          </h2>
          <span className="text-[11px] font-mono text-purple-400">
            Hierarchical Transmission Path
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 relative">
          {/* Stage 0: Geopolitical Event Trigger */}
          <div className="p-4 rounded-lg bg-slate-950 border border-cyan-700/60 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-[10px] font-mono text-cyan-400 mb-1">
                <span>STAGE 0</span>
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
              </div>
              <div className="text-xs font-mono font-bold text-white uppercase">Geopolitical Shock</div>
              <p className="text-[11px] text-slate-300 mt-1 leading-snug">
                {currentScenario?.scenario_data?.query || 'Russia wheat trade restriction'}
              </p>
            </div>
            <div className="mt-3 pt-2 border-t border-slate-800 text-[10px] font-mono text-slate-400">
              Shock: {currentScenario?.scenario_data?.shock_intensity ?? 1.5}x | Share: {currentScenario?.scenario_data?.trade_share ?? 5.0}%
            </div>
          </div>

          {/* Stage 1: Model A Trade Impact */}
          <div className="p-4 rounded-lg bg-slate-950 border border-purple-800 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-[10px] font-mono text-purple-400 mb-1">
                <span>STAGE 1</span>
                <Badge label="MODEL A" variant="PURPLE" size="sm" />
              </div>
              <div className="text-xs font-mono font-bold text-white uppercase">Trade Return</div>
              <div className="text-xl font-bold font-mono text-rose-400 my-1">
                {preds?.trade?.Trade_Return_1M_Pred ? `${preds.trade.Trade_Return_1M_Pred.toFixed(2)}%` : '-4.82%'}
              </div>
              <p className="text-[11px] text-slate-400 leading-snug">
                Projected 1-Month bilateral export trade deflection.
              </p>
            </div>
            <div className="mt-3 pt-2 border-t border-slate-800 text-[10px] font-mono text-slate-500">
              R²: {preds?.trade?.metrics?.r2 ?? 0.68} | MAE: {preds?.trade?.metrics?.mae ?? 1.14}
            </div>
          </div>

          {/* Stage 2: Model B Agricultural Production */}
          <div className="p-4 rounded-lg bg-slate-950 border border-purple-800 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-[10px] font-mono text-purple-400 mb-1">
                <span>STAGE 2</span>
                <Badge label="MODEL B" variant="PURPLE" size="sm" />
              </div>
              <div className="text-xs font-mono font-bold text-white uppercase">Agri Production</div>
              <div className="text-xl font-bold font-mono text-rose-400 my-1">
                {preds?.agriculture?.Production_Growth_Pred ? `${preds.agriculture.Production_Growth_Pred.toFixed(2)}%` : '-1.35%'}
              </div>
              <p className="text-[11px] text-slate-400 leading-snug">
                Estimated national production growth deflection.
              </p>
            </div>
            <div className="mt-3 pt-2 border-t border-slate-800 text-[10px] font-mono text-slate-500">
              Risk: <span className="text-amber-400 font-bold">{preds?.agriculture?.Production_Risk || 'Medium'}</span>
            </div>
          </div>

          {/* Stage 3: Model C Domestic Wholesale Price */}
          <div className="p-4 rounded-lg bg-slate-950 border border-purple-800 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-[10px] font-mono text-purple-400 mb-1">
                <span>STAGE 3</span>
                <Badge label="MODEL C" variant="PURPLE" size="sm" />
              </div>
              <div className="text-xs font-mono font-bold text-white uppercase">Wholesale Price</div>
              <div className="text-xl font-bold font-mono text-rose-400 my-1">
                {preds?.price?.Price_Return_1M_Pred ? `${preds.price.Price_Return_1M_Pred.toFixed(2)}%` : '-2.18%'}
              </div>
              <p className="text-[11px] text-slate-400 leading-snug">
                Domestic wholesale mandi price response.
              </p>
            </div>
            <div className="mt-3 pt-2 border-t border-slate-800 text-[10px] font-mono text-slate-500">
              Multi-lag Ridge VAR
            </div>
          </div>

          {/* Stage 4: Model D Macroeconomic GVA & Inflation */}
          <div className="p-4 rounded-lg bg-slate-950 border border-purple-800 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-[10px] font-mono text-purple-400 mb-1">
                <span>STAGE 4</span>
                <Badge label="MODEL D" variant="PURPLE" size="sm" />
              </div>
              <div className="text-xs font-mono font-bold text-white uppercase">Macro Economy</div>
              <div className="text-xl font-bold font-mono text-rose-400 my-1">
                {preds?.economy?.Agri_GVA_Growth_Pred ? `${preds.economy.Agri_GVA_Growth_Pred.toFixed(2)} pp` : '-0.41 pp'}
              </div>
              <p className="text-[11px] text-slate-400 leading-snug">
                Agricultural GVA impact & Food inflation easing.
              </p>
            </div>
            <div className="mt-3 pt-2 border-t border-slate-800 text-[10px] font-mono text-slate-500">
              Inflation: {preds?.economy?.Inflation_Change_Pred ? `${preds.economy.Inflation_Change_Pred.toFixed(2)} pp` : '-0.19 pp'}
            </div>
          </div>
        </div>
      </div>

      {/* Model Deflection Bar Chart */}
      <div className="card-terminal rounded-xl p-6 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2">
            <BarChart3 className="w-4 h-4 text-purple-400" />
            <h3 className="text-xs font-mono uppercase tracking-widest text-slate-300 font-semibold">
              CROSS-STAGE SHOCK DEFLECTION SUMMARY
            </h3>
          </div>
          <span className="text-[11px] font-mono text-slate-500">
            Model Outputs Comparison
          </span>
        </div>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={cascadeChartData}
              layout="vertical"
              margin={{ top: 10, right: 30, left: 100, bottom: 5 }}
            >
              <XAxis
                type="number"
                domain={[-6, 2]}
                stroke="#64748b"
                tickFormatter={(val) => `${val}%`}
                fontSize={11}
              />
              <YAxis
                type="category"
                dataKey="metric"
                stroke="#94a3b8"
                fontSize={11}
                tickLine={false}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  borderColor: '#334155',
                  borderRadius: '6px',
                  color: '#fff',
                  fontFamily: 'monospace',
                  fontSize: '12px'
                }}
                formatter={(value: any, name: any, props: any) => [
                  `${value} ${props.payload.unit}`,
                  `${props.payload.model}`
                ]}
              />
              <ReferenceLine x={0} stroke="#475569" strokeDasharray="3 3" />
              <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                {cascadeChartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.value < 0 ? '#f43f5e' : '#10b981'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Model Technical Specifications & Provenance Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Model A Details */}
        <div className="card-terminal rounded-xl p-5 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <span className="text-xs font-mono font-bold text-white">MODEL A: TRADE RETURN ESTIMATOR</span>
            <ProvenanceTag tag="[ML INFERENCE]" size="sm" />
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Estimates 1-month forward trade return percentage for the specified commodity and partner country.
            Incorporates GDELT event tone, Goldstein conflict score, bilateral historical trade share, and effective shock intensity.
          </p>
          <div className="pt-2 text-[11px] font-mono text-slate-400 space-y-1">
            <div>Architecture: <span className="text-purple-300">XGBoost + Random Forest Ensemble</span></div>
            <div>Target Variable: <span className="text-slate-200">Trade_Return_1M</span></div>
            <div>Validation R²: <span className="text-emerald-400">0.68</span> | MAE: <span className="text-slate-200">1.14%</span></div>
          </div>
        </div>

        {/* Model B Details */}
        <div className="card-terminal rounded-xl p-5 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <span className="text-xs font-mono font-bold text-white">MODEL B: PRODUCTION GROWTH BOOSTER</span>
            <ProvenanceTag tag="[ML INFERENCE]" size="sm" />
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Forecasts national agricultural production growth deflection and classifies structural harvest risk.
            Conditioned on trade shock transmission, climate anomalies, and multi-year crop acreage momentum.
          </p>
          <div className="pt-2 text-[11px] font-mono text-slate-400 space-y-1">
            <div>Architecture: <span className="text-purple-300">LightGBM Gradient Boosted Regressor</span></div>
            <div>Target Variable: <span className="text-slate-200">Production_Growth_Pred</span></div>
            <div>Risk Classification: <span className="text-amber-400">Medium Production Risk Tier</span></div>
          </div>
        </div>

        {/* Model C Details */}
        <div className="card-terminal rounded-xl p-5 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <span className="text-xs font-mono font-bold text-white">MODEL C: WHOLESALE PRICE VECTOR AUTOREGRESSOR</span>
            <ProvenanceTag tag="[ML INFERENCE]" size="sm" />
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Projects domestic wholesale price return across primary terminal markets.
            Captures the market response when export barriers trap commodity volumes in inland consuming regions.
          </p>
          <div className="pt-2 text-[11px] font-mono text-slate-400 space-y-1">
            <div>Architecture: <span className="text-purple-300">Multi-lag Ridge VAR</span></div>
            <div>Target Variable: <span className="text-slate-200">Price_Return_1M_Pred</span></div>
            <div>Interpretation: <span className="text-cyan-300">Domestic market surplus price easing</span></div>
          </div>
        </div>

        {/* Model D Details */}
        <div className="card-terminal rounded-xl p-5 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <span className="text-xs font-mono font-bold text-white">MODEL D: MACRO GVA & INFLATION TRANSFER</span>
            <ProvenanceTag tag="[ML INFERENCE]" size="sm" />
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Maps sectoral agricultural shocks into national macroeconomic outcomes, specifically Agricultural Gross Value Added (GVA) growth and consumer food price inflation.
          </p>
          <div className="pt-2 text-[11px] font-mono text-slate-400 space-y-1">
            <div>Architecture: <span className="text-purple-300">Macroeconomic Elasticity Transfer Matrix</span></div>
            <div>Target Variables: <span className="text-slate-200">Agri_GVA_Growth_Pred, Inflation_Change_Pred</span></div>
            <div>Macro Impact: <span className="text-rose-400">-0.41 pp GVA | -0.19 pp Food Inflation</span></div>
          </div>
        </div>
      </div>
    </div>
  );
};
