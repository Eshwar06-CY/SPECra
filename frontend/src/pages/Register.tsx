import React, { useState } from 'react';
import { ArrowRight, Lock, Mail, Building, User as UserIcon, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useApp } from '../context/AppContext';
import { SpecraLogo } from '../components/ui/SpecraLogo';

export const Register: React.FC = () => {
  const { register } = useAuth();
  const { setActiveTab } = useApp();
  const [fullName, setFullName] = useState<string>('');
  const [organization, setOrganization] = useState<string>('');
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [agree, setAgree] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!agree) return;
    setLoading(true);
    try {
      await register(fullName, organization, email, password);
      setActiveTab('dashboard');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#07090e] text-slate-100 flex items-center justify-center p-6 relative overflow-hidden font-sans">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-blue-500/10 blur-[140px] pointer-events-none" />

      <div className="w-full max-w-md space-y-6 relative z-10">
        <div className="text-center space-y-2">
          <div
            onClick={() => setActiveTab('landing')}
            className="inline-flex items-center justify-center cursor-pointer mb-1"
          >
            <SpecraLogo size="lg" layout="stacked" showTagline />
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Create your workspace.</h2>
          <p className="text-xs text-slate-400">Start analyzing industrial product catalogs in minutes.</p>
        </div>

        <div className="specra-panel rounded-3xl p-8 border border-slate-800 space-y-5">
          <form onSubmit={handleSubmit} className="space-y-3.5">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-300">Full Name</label>
              <div className="relative">
                <UserIcon className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. Jordan Hayes"
                  className="specra-input w-full pl-10 pr-4 py-2 rounded-xl text-xs"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-300">Organization / Company</label>
              <div className="relative">
                <Building className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  required
                  value={organization}
                  onChange={(e) => setOrganization(e.target.value)}
                  placeholder="e.g. Acme Industrial Supply"
                  className="specra-input w-full pl-10 pr-4 py-2 rounded-xl text-xs"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-300">Work Email</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="jordan@company.com"
                  className="specra-input w-full pl-10 pr-4 py-2 rounded-xl text-xs"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-300">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Create a strong password"
                  className="specra-input w-full pl-10 pr-4 py-2 rounded-xl text-xs"
                />
              </div>
            </div>

            <div className="pt-1">
              <label className="flex items-start gap-2 text-[11px] text-slate-400 cursor-pointer">
                <input
                  type="checkbox"
                  checked={agree}
                  onChange={(e) => setAgree(e.target.checked)}
                  className="rounded bg-slate-800 border-slate-700 text-cyan-500 mt-0.5"
                />
                <span>I agree to SPECra Workspace Terms & Data Handling Principles.</span>
              </label>
            </div>

            <button
              type="submit"
              disabled={loading || !agree}
              className="w-full py-3 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs transition-all shadow-lg shadow-cyan-500/20 flex items-center justify-center gap-2 cursor-pointer mt-2 disabled:opacity-50"
            >
              {loading ? 'Creating...' : 'Create workspace'}
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </form>

          <div className="text-center pt-2 border-t border-slate-800">
            <span className="text-xs text-slate-400">Already have an account? </span>
            <button
              onClick={() => setActiveTab('login')}
              className="text-xs text-cyan-400 font-bold hover:text-cyan-300"
            >
              Sign in
            </button>
          </div>
        </div>

        <div className="text-center text-[11px] text-slate-500 flex items-center justify-center gap-2">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          <span>Private Workspace • Team DEADLOCK • UniHack 2026</span>
        </div>
      </div>
    </div>
  );
};
