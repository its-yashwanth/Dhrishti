import React from 'react';
import { SeverityLevel } from '../../types/drishti';

interface BadgeProps {
  label: string;
  variant?: SeverityLevel | 'PURPLE' | 'CYAN' | 'SLATE';
  size?: 'sm' | 'md';
  icon?: React.ReactNode;
  pulse?: boolean;
}

export const Badge: React.FC<BadgeProps> = ({
  label,
  variant = 'INFO',
  size = 'md',
  icon,
  pulse = false
}) => {
  const getStyles = () => {
    switch (variant) {
      case 'LOW':
        return 'bg-emerald-950/80 text-emerald-300 border-emerald-800/80';
      case 'MODERATE':
        return 'bg-amber-950/80 text-amber-300 border-amber-800/80';
      case 'HIGH':
        return 'bg-orange-950/80 text-orange-300 border-orange-800/80';
      case 'CRITICAL':
      case 'VERY HIGH':
        return 'bg-rose-950/90 text-rose-300 border-rose-800/80';
      case 'PURPLE':
        return 'bg-purple-950/80 text-purple-300 border-purple-800/80';
      case 'CYAN':
        return 'bg-cyan-950/80 text-cyan-300 border-cyan-800/80';
      case 'SLATE':
      default:
        return 'bg-slate-900 text-slate-300 border-slate-700';
    }
  };

  const sizeClasses = size === 'sm' ? 'text-[10px] px-1.5 py-0.5' : 'text-xs px-2 py-0.5';

  return (
    <span
      className={`inline-flex items-center space-x-1 font-mono font-medium rounded border ${sizeClasses} ${getStyles()}`}
    >
      {pulse && (
        <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse mr-1" />
      )}
      {icon && <span className="shrink-0">{icon}</span>}
      <span>{label}</span>
    </span>
  );
};
