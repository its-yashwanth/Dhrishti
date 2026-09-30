import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Sparkles,
  GitCommitHorizontal,
  Globe2,
  MapPin,
  Users,
  ShieldCheck,
  Database,
  FileText,
  Network,
  Info
} from 'lucide-react';

interface NavItem {
  name: string;
  path: string;
  icon: React.ElementType;
  badge?: string;
  badgeColor?: string;
}

const NAV_ITEMS: NavItem[] = [
  { name: 'Dashboard', path: '/', icon: LayoutDashboard },
  { name: 'Event Analysis', path: '/event-analysis', icon: Sparkles, badge: 'NL Ingest', badgeColor: 'bg-cyan-950 text-cyan-400 border-cyan-800' },
  { name: 'Impact Cascade', path: '/cascade', icon: GitCommitHorizontal, badge: 'M-A → D', badgeColor: 'bg-purple-950 text-purple-400 border-purple-800' },
  { name: 'Supply Chain', path: '/supply-chain', icon: Globe2, badge: '3D Globe', badgeColor: 'bg-sky-950 text-sky-400 border-sky-800' },
  { name: 'Vulnerability', path: '/vulnerability', icon: MapPin, badge: 'RAVS', badgeColor: 'bg-amber-950 text-amber-400 border-amber-800' },
  { name: 'Stakeholder Impact', path: '/stakeholders', icon: Users },
  { name: 'Mitigation & Actions', path: '/mitigation', icon: ShieldCheck, badge: 'Playbook', badgeColor: 'bg-emerald-950 text-emerald-400 border-emerald-800' },
  { name: 'Evidence & Provenance', path: '/evidence', icon: Database },
  { name: 'Decision Report', path: '/report', icon: FileText },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 bg-[#0a0f1d] border-r border-slate-800 flex flex-col shrink-0 select-none">
      {/* Navigation Section Header */}
      <div className="px-4 py-3 border-b border-slate-800/80 flex items-center justify-between">
        <span className="text-[10px] font-mono uppercase tracking-widest text-slate-500 font-semibold">
          DECISION PLATFORM
        </span>
        <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 shadow-glow-cyan animate-pulse" />
      </div>

      {/* Main Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) => `
                group flex items-center justify-between px-3 py-2.5 rounded-md text-xs font-medium transition-all duration-150
                ${isActive
                  ? 'bg-gradient-to-r from-cyan-950/80 to-slate-900 border-l-2 border-cyan-400 text-cyan-200 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60 border-l-2 border-transparent'
                }
              `}
            >
              <div className="flex items-center space-x-3">
                <Icon className="w-4 h-4 shrink-0 transition-colors group-hover:text-cyan-400" />
                <span className="tracking-tight">{item.name}</span>
              </div>
              {item.badge && (
                <span className={`text-[10px] font-mono px-1.5 py-0.2 rounded border font-semibold ${item.badgeColor || 'bg-slate-800 text-slate-400 border-slate-700'}`}>
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Footer / System Architecture */}
      <div className="p-3 border-t border-slate-800 bg-[#070b14]/60 space-y-1">
        <NavLink
          to="/architecture"
          className={({ isActive }) => `
            flex items-center space-x-3 px-3 py-2 rounded-md text-xs font-medium transition-colors
            ${isActive
              ? 'bg-purple-950/50 border-l-2 border-purple-400 text-purple-200'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50 border-l-2 border-transparent'
            }
          `}
        >
          <Network className="w-4 h-4 text-purple-400 shrink-0" />
          <div>
            <div className="text-slate-200 font-mono text-[11px] font-semibold">System Architecture</div>
            <div className="text-[10px] text-slate-500">Models A-D & Agent Engine</div>
          </div>
        </NavLink>

        <div className="pt-2 px-3 flex items-center justify-between text-[10px] text-slate-500 font-mono">
          <span className="flex items-center space-x-1">
            <Info className="w-3 h-3 text-slate-600" />
            <span>Drishti Framework</span>
          </span>
          <span className="text-slate-600">Phase 1 Capstone</span>
        </div>
      </div>
    </aside>
  );
};
