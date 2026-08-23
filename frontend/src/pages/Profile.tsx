import React, { useState } from 'react';
import {
  User,
  Building,
  Mail,
  Shield,
  Key,
  LogOut,
  CheckCircle2,
  Lock,
  Smartphone,
  Sparkles,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useApp } from '../context/AppContext';

export const Profile: React.FC = () => {
  const { user, logout, updateProfile } = useAuth();
  const { setActiveTab } = useApp();
  const [name, setName] = useState(user?.name || 'Alex Rivera');
  const [org, setOrg] = useState(user?.organization || 'Apex Industrial Supply Co.');
  const [email] = useState(user?.email || 'alex.rivera@industrialtech.io');
  const [savedSuccess, setSavedSuccess] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    updateProfile({ name, organization: org });
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  const handleLogout = () => {
    logout();
    setActiveTab('landing');
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-12">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Workspace Profile</h2>
          <p className="text-xs text-slate-400 mt-1">
            Manage your personal credentials, company organization, and workspace security settings.
          </p>
        </div>

        <button
          onClick={handleLogout}
          className="px-4 py-2 rounded-xl text-xs font-semibold bg-rose-500/10 text-rose-300 hover:bg-rose-500/20 border border-rose-500/20 flex items-center gap-1.5 transition-colors"
        >
          <LogOut className="w-3.5 h-3.5" />
          <span>Sign out</span>
        </button>
      </div>

      {/* Profile Information Form */}
      <div className="specra-panel rounded-3xl p-8 border border-slate-800 space-y-6">
        <div className="flex items-center gap-4 border-b border-slate-800 pb-6">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center text-xl font-bold text-white shadow-lg shadow-cyan-500/20">
            {name.charAt(0)}
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">{name}</h3>
            <p className="text-xs text-slate-400 font-mono mt-0.5">{email}</p>
            <div className="inline-flex items-center gap-1.5 mt-2 px-2.5 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 text-[10px] font-semibold">
              <Sparkles className="w-3 h-3" />
              <span>{user?.role || 'Catalog Operations Lead'}</span>
            </div>
          </div>
        </div>

        <form onSubmit={handleSave} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300">Full Name</label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="specra-input w-full pl-10 pr-4 py-2.5 rounded-xl text-xs"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300">Organization / Company</label>
              <div className="relative">
                <Building className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={org}
                  onChange={(e) => setOrg(e.target.value)}
                  className="specra-input w-full pl-10 pr-4 py-2.5 rounded-xl text-xs"
                />
              </div>
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300">Email Address (Primary Workspace ID)</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="email"
                disabled
                value={email}
                className="specra-input w-full pl-10 pr-4 py-2.5 rounded-xl text-xs opacity-60 cursor-not-allowed"
              />
            </div>
          </div>

          <div className="flex items-center justify-between pt-2">
            {savedSuccess ? (
              <span className="text-xs font-semibold text-emerald-400 flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4" />
                Profile updated successfully!
              </span>
            ) : (
              <span className="text-[11px] text-slate-500">Changes are saved to your current browser workspace.</span>
            )}
            <button
              type="submit"
              className="px-6 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs transition-all shadow-md shadow-cyan-500/20"
            >
              Save Changes
            </button>
          </div>
        </form>
      </div>

      {/* Security & Access Panel */}
      <div className="specra-panel rounded-3xl p-8 border border-slate-800 space-y-6">
        <div className="flex items-center gap-2 text-sm font-bold text-white border-b border-slate-800 pb-3">
          <Shield className="w-4 h-4 text-cyan-400" />
          <span>Security & Authentication Control</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Key className="w-4 h-4 text-indigo-400" />
                <span className="text-xs font-bold text-white">Password & Credentials</span>
              </div>
            </div>
            <p className="text-xs text-slate-400">
              Manage your workspace access passphrase.
            </p>
            <button className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 transition-colors">
              Change password
            </button>
          </div>

          <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Smartphone className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-bold text-white">Active Sessions</span>
              </div>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 font-semibold border border-emerald-500/20">
                1 Active
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Current browser on Windows (Local Dev).
            </p>
            <button
              onClick={handleLogout}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-rose-300 transition-colors"
            >
              Sign out of all devices
            </button>
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-cyan-950/20 border border-cyan-500/30 text-xs text-slate-300 space-y-1">
          <div className="font-bold text-white flex items-center gap-1.5">
            <Lock className="w-3.5 h-3.5 text-cyan-400" />
            <span>Enterprise Workspace Notice</span>
          </div>
          <p className="text-[11px] text-slate-400">
            SPECra is configured with local workspace isolation for UniHack 2026. Built by Team DEADLOCK.
          </p>
        </div>
      </div>
    </div>
  );
};
