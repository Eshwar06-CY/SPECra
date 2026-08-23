import React from 'react';
import { Search } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useApp } from '../../context/AppContext';

interface TopbarProps {
  title: string;
  subtitle: string;
}

export const Topbar: React.FC<TopbarProps> = ({ title, subtitle }) => {
  const { user } = useAuth();
  const { setActiveTab } = useApp();

  return (
    <header className="h-18 border-b border-white/5 bg-[#090d16]/80 backdrop-blur-xl px-6 md:px-8 flex items-center justify-between sticky top-0 z-20">
      {/* Title & Subtitle */}
      <div className="flex-1 min-w-0 pr-4">
        <h1 className="text-base font-bold text-white tracking-tight truncate">
          {title}
        </h1>
        <p className="text-xs text-slate-400 truncate mt-0.5">
          {subtitle}
        </p>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-4 flex-shrink-0">
        {/* Quick Search */}
        <div className="relative hidden md:block w-48">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search catalog items..."
            className="specra-input w-full pl-8 pr-3 py-1.5 rounded-lg text-xs"
          />
        </div>

        {/* AI Health Badge */}
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-[11px] font-medium text-cyan-300">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
          <span>Gemini 3.5 Flash Lite Active</span>
        </div>

        {/* User Avatar */}
        <button
          onClick={() => setActiveTab('profile')}
          className="flex items-center gap-2 p-1 rounded-xl hover:bg-slate-800/60 transition-colors"
        >
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center font-bold text-xs text-white shadow-sm shadow-cyan-500/20">
            {user?.name?.charAt(0) || 'A'}
          </div>
          <span className="text-xs font-semibold text-slate-200 hidden lg:inline-block">
            {user?.name?.split(' ')[0] || 'Alex'}
          </span>
        </button>
      </div>
    </header>
  );
};
