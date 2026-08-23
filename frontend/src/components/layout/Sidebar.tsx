import React from 'react';
import {
  LayoutDashboard,
  FolderKanban,
  FilePlus2,
  Table as TableIcon,
  Download,
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { useAuth } from '../../context/AuthContext';
import { SpecraLogo } from '../ui/SpecraLogo';

export const Sidebar: React.FC = () => {
  const { activeTab, setActiveTab } = useApp();
  const { user } = useAuth();

  const navItems = [
    {
      id: 'dashboard',
      label: 'Overview',
      icon: LayoutDashboard,
    },
    {
      id: 'jobs',
      label: 'My Catalogs',
      icon: FolderKanban,
    },
    {
      id: 'upload',
      label: 'New Analysis',
      icon: FilePlus2,
      isAction: true,
    },
    {
      id: 'results',
      label: 'Results & Intelligence',
      icon: TableIcon,
    },
    {
      id: 'export',
      label: 'Exports',
      icon: Download,
    },
  ];

  return (
    <aside className="w-64 border-r border-white/5 bg-[#090d16] flex flex-col justify-between p-4 flex-shrink-0 select-none z-30">
      <div className="space-y-6">
        {/* Brand Logo */}
        <div
          onClick={() => setActiveTab('landing')}
          className="px-2 py-1 cursor-pointer group"
        >
          <SpecraLogo size="sm" showTagline />
        </div>

        {/* Workspace Chip */}
        <div className="px-3 py-2 rounded-xl bg-slate-900/80 border border-slate-800/80">
          <div className="text-[10px] text-slate-400 uppercase font-semibold">Workspace</div>
          <div className="text-xs font-bold text-slate-200 truncate mt-0.5">
            {user?.organization || 'Apex Industrial Supply Co.'}
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive =
              activeTab === item.id ||
              (item.id === 'upload' &&
                (activeTab === 'understand' ||
                  activeTab === 'requirements' ||
                  activeTab === 'process' ||
                  activeTab === 'pipeline'));

            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                  isActive
                    ? 'bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 shadow-sm shadow-cyan-500/10'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                <span className="flex-1 text-left">{item.label}</span>
                {item.isAction && !isActive && (
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 font-bold">
                    +
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Bottom Profile & Footer */}
      <div className="space-y-2 pt-4 border-t border-slate-800/80">
        <button
          onClick={() => setActiveTab('profile')}
          className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs transition-all ${
            activeTab === 'profile'
              ? 'bg-slate-800 text-white'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
          }`}
        >
          <div className="w-7 h-7 rounded-lg bg-cyan-500/20 text-cyan-300 font-bold flex items-center justify-center text-xs">
            {user?.name?.charAt(0) || 'A'}
          </div>
          <div className="flex-1 text-left truncate">
            <div className="font-semibold text-slate-200 text-xs truncate">
              {user?.name || 'Alex Rivera'}
            </div>
            <div className="text-[10px] text-slate-400 truncate">Settings & Profile</div>
          </div>
        </button>

        <div className="flex items-center justify-between px-2 pt-1 text-[10px] text-slate-400">
          <span>By Team DEADLOCK</span>
          <span>UniHack 2026</span>
        </div>
      </div>
    </aside>
  );
};
