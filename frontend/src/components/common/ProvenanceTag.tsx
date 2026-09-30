import React from 'react';
import { Database, Cpu, Network, UserCheck, Sparkles, FileSpreadsheet } from 'lucide-react';

interface ProvenanceTagProps {
  tag: string;
  size?: 'sm' | 'md';
}

export const ProvenanceTag: React.FC<ProvenanceTagProps> = ({ tag, size = 'sm' }) => {
  const getIcon = () => {
    if (tag.includes('ML')) return <Cpu className="w-3 h-3 text-purple-400" />;
    if (tag.includes('GRAPH')) return <Network className="w-3 h-3 text-cyan-400" />;
    if (tag.includes('PORT') || tag.includes('AGRICULTURE')) return <FileSpreadsheet className="w-3 h-3 text-emerald-400" />;
    if (tag.includes('USER') || tag.includes('CLI')) return <UserCheck className="w-3 h-3 text-amber-400" />;
    if (tag.includes('LLM')) return <Sparkles className="w-3 h-3 text-sky-400" />;
    return <Database className="w-3 h-3 text-slate-400" />;
  };

  const sizeClass = size === 'sm' ? 'text-[10px] px-1.5 py-0.5' : 'text-xs px-2 py-0.5';

  return (
    <span className={`inline-flex items-center space-x-1.5 font-mono bg-slate-950/70 border border-slate-800 text-slate-300 rounded ${sizeClass}`}>
      {getIcon()}
      <span className="tracking-tight">{tag}</span>
    </span>
  );
};
