import React from 'react';
import { CheckCircle2, Loader2, Circle, AlertCircle } from 'lucide-react';
import { PipelineStageEvent } from '../../services/api';

interface ProcessingPipelineProps {
  currentStage?: PipelineStageEvent['stage'];
  stagesStatus?: Record<string, 'pending' | 'active' | 'completed' | 'error'>;
}

const ORDERED_STAGES = [
  { id: 'EVENT_INTELLIGENCE', label: 'EVENT INTELLIGENCE', desc: 'GDELT DOC 2.0 Ingest' },
  { id: 'STRUCTURED_EVENT', label: 'STRUCTURED EVENT', desc: 'HS4 & Canonical Direction' },
  { id: 'ML_CASCADE', label: 'ML CASCADE', desc: 'Models A → B → C → D' },
  { id: 'SUPPLY_CHAIN', label: 'SUPPLY CHAIN', desc: 'NetworkX MultiDiGraph' },
  { id: 'VULNERABILITY', label: 'VULNERABILITY', desc: 'District RAVS Index' },
  { id: 'STAKEHOLDER', label: 'STAKEHOLDER IMPACT', desc: 'Distributional Effects' },
  { id: 'MITIGATION', label: 'MITIGATION', desc: 'Action Playbooks' },
];

export const ProcessingPipeline: React.FC<ProcessingPipelineProps> = ({
  currentStage,
  stagesStatus = {}
}) => {
  return (
    <div className="card-terminal rounded-xl p-5 border border-slate-800">
      <div className="flex items-center justify-between mb-4 border-b border-slate-800/80 pb-3">
        <div className="flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
          <h3 className="text-xs font-mono uppercase tracking-widest text-slate-300 font-semibold">
            ORCHESTRATOR EXECUTION CASCADE
          </h3>
        </div>
        <span className="text-[11px] font-mono text-cyan-400">
          7-Stage Pipeline
        </span>
      </div>

      {/* Pipeline Stages Progress Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
        {ORDERED_STAGES.map((stg, idx) => {
          const status = stagesStatus[stg.id] || (currentStage === stg.id ? 'active' : 'pending');

          return (
            <div
              key={stg.id}
              className={`p-3 rounded-lg border transition-all duration-200 flex flex-col justify-between ${
                status === 'completed'
                  ? 'bg-emerald-950/20 border-emerald-800/60 text-emerald-300'
                  : status === 'active'
                  ? 'bg-cyan-950/40 border-cyan-500 text-cyan-200 shadow-glow-cyan'
                  : status === 'error'
                  ? 'bg-rose-950/30 border-rose-800 text-rose-300'
                  : 'bg-slate-900/40 border-slate-800/80 text-slate-500'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[10px] font-mono font-bold text-slate-400">
                  0{idx + 1}
                </span>
                {status === 'completed' && <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />}
                {status === 'active' && <Loader2 className="w-4 h-4 text-cyan-400 animate-spin shrink-0" />}
                {status === 'pending' && <Circle className="w-3.5 h-3.5 text-slate-600 shrink-0" />}
                {status === 'error' && <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />}
              </div>

              <div>
                <div className="text-[11px] font-mono font-bold tracking-tight leading-tight">
                  {stg.label}
                </div>
                <div className="text-[9px] text-slate-400 font-sans mt-0.5 truncate">
                  {stg.desc}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
