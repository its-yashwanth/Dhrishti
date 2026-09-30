import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import {
  Database,
  FileSearch,
  ExternalLink,
  Layers,
  Search,
  Filter,
  CheckCircle2,
  FileSpreadsheet,
  Cpu,
  Radio,
  BookOpen
} from 'lucide-react';
import { Badge } from '../components/common/Badge';
import { ProvenanceTag } from '../components/common/ProvenanceTag';
import { DrishtiAnalysisResult, EvidenceItem } from '../types/drishti';

interface OutletContextType {
  currentScenario: DrishtiAnalysisResult;
}

export const EvidencePage: React.FC = () => {
  const { currentScenario } = useOutletContext<OutletContextType>();
  const evidenceList: EvidenceItem[] = currentScenario?.evidence_list || [];

  const [filterType, setFilterType] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const filteredEvidence = evidenceList.filter((item) => {
    const matchesFilter = filterType === 'ALL' || item.source_type.includes(filterType);
    const matchesSearch =
      item.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.source.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.evidence.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center space-x-2 text-cyan-400 font-mono text-xs mb-1">
            <Database className="w-4 h-4 text-cyan-400" />
            <span>DATA LINEAGE & EVIDENCE REPOSITORY</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Evidence, Datasets & Model Provenance
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-3xl">
            Complete transparency registry connecting econometric forecasts and agent advisories to verified official datasets, ML model checkpoints, and GDELT live news context.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <Badge label="RAG-READY SCHEMA" variant="CYAN" size="sm" />
          <Badge label="STRICT AUDIT TRAILS" variant="PURPLE" size="sm" />
        </div>
      </div>

      {/* RAG-Ready Architecture Note */}
      <div className="p-3.5 rounded-lg bg-cyan-950/20 border border-cyan-800/60 flex items-start space-x-3 text-xs text-cyan-200">
        <FileSearch className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          <strong className="text-cyan-300 font-semibold">Modular Evidence Architecture:</strong> Designed for drop-in RAG integration. When vector search retrieval is activated, document chunks and semantic relevance scores seamlessly populate this repository view.
        </p>
      </div>

      {/* Filter and Search Bar */}
      <div className="card-terminal rounded-xl p-4 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-2">
          {['ALL', 'Dataset', 'ML Econometric', 'GDELT', 'MultiDiGraph'].map((type) => (
            <button
              key={type}
              onClick={() => setFilterType(type)}
              className={`px-3 py-1 rounded-md text-xs font-mono font-medium transition-colors cursor-pointer ${
                filterType === type
                  ? 'bg-cyan-950 text-cyan-300 border border-cyan-800 shadow-glow-cyan'
                  : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              {type === 'ALL' ? 'All Sources' : type}
            </button>
          ))}
        </div>

        <div className="relative">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search evidence & citations..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-md pl-8 pr-3 py-1.5 text-xs text-white font-mono focus:outline-none focus:border-cyan-500 w-full sm:w-64"
          />
        </div>
      </div>

      {/* Evidence Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredEvidence.map((item, idx) => (
          <div
            key={item.id || idx}
            className="card-terminal rounded-xl p-5 border border-slate-800 hover:border-slate-700 transition-colors flex flex-col justify-between space-y-4"
          >
            <div>
              <div className="flex items-center justify-between border-b border-slate-800 pb-2.5 mb-3">
                <span className="text-[10px] font-mono uppercase text-slate-400 font-bold">
                  {item.source_type}
                </span>
                <ProvenanceTag tag={item.provenance_tag} size="sm" />
              </div>

              <h3 className="text-sm font-bold font-mono text-white mb-1">
                {item.title}
              </h3>
              <div className="text-[11px] text-cyan-400 font-mono mb-2">
                Origin: {item.source}
              </div>

              <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-3 rounded border border-slate-800/80 mb-3">
                "{item.evidence}"
              </p>

              <div className="text-xs text-slate-400">
                <strong className="text-slate-300 font-mono text-[11px]">Utilized By:</strong> {item.used_for}
              </div>
            </div>

            <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-[10px] font-mono text-slate-500">
              <span>Coverage: {item.coverage_period || 'Baseline Data'}</span>
              {item.citation && (
                <span className="truncate max-w-[200px]" title={item.citation}>
                  Cite: {item.citation}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
