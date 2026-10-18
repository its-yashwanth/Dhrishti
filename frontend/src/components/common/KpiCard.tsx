import React from 'react';
import { TrendingUp, TrendingDown, Minus, Info } from 'lucide-react';
import { Badge } from './Badge';
import { ProvenanceTag } from './ProvenanceTag';
import { SeverityLevel } from '../../types/drishti';

interface KpiCardProps {
  title: string;
  value: string | number;
  unit?: string;
  change?: string;
  direction?: 'up' | 'down' | 'neutral';
  severity?: SeverityLevel;
  subtitle?: string;
  provenance?: string;
  modelBadge?: string;
  footerNote?: string;
  accentColor?: 'cyan' | 'purple' | 'green' | 'amber' | 'red';
}

export const KpiCard: React.FC<KpiCardProps> = ({
  title,
  value,
  unit,
  change,
  direction,
  severity,
  subtitle,
  provenance,
  modelBadge,
  footerNote,
  accentColor = 'cyan'
}) => {
  const getBorderColor = () => {
    switch (accentColor) {
      case 'purple': return 'hover:border-purple-500/50';
      case 'green': return 'hover:border-emerald-500/50';
      case 'amber': return 'hover:border-amber-500/50';
      case 'red': return 'hover:border-rose-500/50';
      case 'cyan':
      default: return 'hover:border-cyan-500/50';
    }
  };

  return (
    <div
      className={`card-terminal rounded-lg p-4 border border-slate-800/90 transition-all duration-200 ${getBorderColor()} flex flex-col justify-between`}
    >
      <div>
        {/* Top Header */}
        <div className="flex items-center justify-between mb-2">
          <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400 font-medium truncate">
            {title}
          </span>
          <div className="flex items-center space-x-1.5 shrink-0">
            {modelBadge && (
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-purple-950/70 border border-purple-800 text-purple-300">
                {modelBadge}
              </span>
            )}
            {severity && <Badge label={severity} variant={severity} size="sm" />}
          </div>
        </div>

        {/* Primary Metric Value */}
        <div className="flex items-baseline space-x-2 my-1">
          <span className="text-2xl font-bold font-mono text-white tracking-tight">
            {value}
          </span>
          {unit && <span className="text-xs font-mono text-slate-400">{unit}</span>}
          {change && (
            <div className={`flex items-center space-x-0.5 text-xs font-mono font-medium ml-2 ${
              direction === 'down' ? 'text-rose-400' : direction === 'up' ? 'text-emerald-400' : 'text-slate-400'
            }`}>
              {direction === 'down' && <TrendingDown className="w-3.5 h-3.5" />}
              {direction === 'up' && <TrendingUp className="w-3.5 h-3.5" />}
              {direction === 'neutral' && <Minus className="w-3.5 h-3.5" />}
              <span>{change}</span>
            </div>
          )}
        </div>

        {/* Subtitle / Context */}
        {subtitle && (
          <p className="text-xs text-slate-400 mt-1 line-clamp-2 leading-relaxed">
            {subtitle}
          </p>
        )}
      </div>

      {/* Footer / Provenance */}
      <div className="mt-3 pt-2.5 border-t border-slate-800/60 flex items-center justify-between text-[10px]">
        {provenance ? (
          <ProvenanceTag tag={provenance} size="sm" />
        ) : (
          <span className="text-slate-500 font-mono flex items-center space-x-1">
            <Info className="w-3 h-3" />
            <span>Grounded forecast</span>
          </span>
        )}
        {footerNote && (
          <span className="text-slate-500 font-mono truncate max-w-[130px] ml-2 text-right">
            {footerNote}
          </span>
        )}
      </div>
    </div>
  );
};
