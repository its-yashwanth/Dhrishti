import React from 'react';
import { CheckCircle2, Loader2, Circle, AlertCircle, AlertTriangle, RotateCcw } from 'lucide-react';
import { PipelineStageEvent } from '../../services/api';

export interface ProcessingPipelineProps {
  currentStage?: PipelineStageEvent['stage'];
  stagesStatus?: Record<string, 'pending' | 'active' | 'completed' | 'error'>;
  stagesDetail?: Record<string, string>;
  isExecuting?: boolean;
  elapsedSeconds?: number;
  errorMessage?: string | null;
  failedStage?: string | null;
  onRetry?: () => void;
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
  stagesStatus = {},
  stagesDetail = {},
  isExecuting = false,
  elapsedSeconds = 0,
  errorMessage = null,
  failedStage = null,
  onRetry
}) => {
  const isAllComplete = ORDERED_STAGES.every(stg => stagesStatus[stg.id] === 'completed');

  return (
    <div className="card-terminal rounded-xl p-5 border border-slate-800 space-y-4">
      {/* Header bar */}
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
        <div className="flex items-center space-x-2">
          {isExecuting ? (
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse shadow-glow-cyan" />
          ) : errorMessage ? (
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
          ) : isAllComplete ? (
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
          ) : (
            <span className="w-2.5 h-2.5 rounded-full bg-slate-500" />
          )}

          <h3 className="text-xs font-mono uppercase tracking-widest text-slate-300 font-semibold">
            ORCHESTRATOR EXECUTION CASCADE
          </h3>

          {isExecuting && (
            <span className="text-[11px] font-mono text-cyan-400 ml-2 animate-pulse">
              [RUNNING {elapsedSeconds}s]
            </span>
          )}
          {errorMessage && (
            <span className="text-[11px] font-mono text-rose-400 ml-2">
              [EXECUTION HALTED]
            </span>
          )}
          {isAllComplete && !isExecuting && (
            <span className="text-[11px] font-mono text-emerald-400 ml-2">
              [COMPLETED]
            </span>
          )}
        </div>

        <span className="text-[11px] font-mono text-cyan-400">
          7-Stage Pipeline
        </span>
      </div>

      {/* Pipeline Stages Progress Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
        {ORDERED_STAGES.map((stg, idx) => {
          const rawStatus = stagesStatus[stg.id] || (currentStage === stg.id ? 'active' : 'pending');
          // Guard: Never display spinning active loader when execution is not active
          const status = (!isExecuting && rawStatus === 'active')
            ? (errorMessage ? 'error' : 'pending')
            : rawStatus;

          const detailText = stagesDetail[stg.id];

          return (
            <div
              key={stg.id}
              className={`p-3 rounded-lg border transition-all duration-200 flex flex-col justify-between ${
                status === 'completed'
                  ? 'bg-emerald-950/20 border-emerald-800/60 text-emerald-300'
                  : status === 'active'
                  ? 'bg-cyan-950/40 border-cyan-500 text-cyan-200 shadow-glow-cyan'
                  : status === 'error'
                  ? 'bg-rose-950/40 border-rose-600 text-rose-300 shadow-glow-rose'
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
                <div
                  className="text-[9px] text-slate-400 font-sans mt-0.5 truncate"
                  title={detailText || stg.desc}
                >
                  {detailText || stg.desc}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Explicit Error Banner & Safe Retry Action */}
      {errorMessage && (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 rounded-lg bg-rose-950/40 border border-rose-800/80 text-rose-200">
          <div className="flex items-start space-x-2.5">
            <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
            <div>
              <div className="text-xs font-mono font-bold text-rose-300">
                Stage Execution Interrupted: {failedStage || 'Orchestrator Stage Failure'}
              </div>
              <div className="text-xs text-rose-200/90 mt-0.5 font-sans leading-relaxed">
                {errorMessage}
              </div>
            </div>
          </div>

          {onRetry && (
            <button
              onClick={onRetry}
              disabled={isExecuting}
              className="flex items-center justify-center space-x-1.5 px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-mono text-xs font-semibold transition-colors shrink-0 shadow-sm disabled:opacity-50"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Retry Analysis</span>
            </button>
          )}
        </div>
      )}
    </div>
  );
};
