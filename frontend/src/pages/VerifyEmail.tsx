import React, { useState, useEffect } from 'react';
import { CheckCircle2, AlertCircle, ShieldCheck } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { SpecraLogo } from '../components/ui/SpecraLogo';
import { api } from '../api/client';

export const VerifyEmail: React.FC = () => {
  const { setActiveTab } = useApp();
  const [tokenInput, setTokenInput] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [success, setSuccess] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const hash = window.location.hash;
    const search = window.location.search;
    const urlParams = new URLSearchParams(hash.includes('?') ? hash.split('?')[1] : search);
    const tokenParam = urlParams.get('token');

    if (tokenParam) {
      setTokenInput(tokenParam);
      verify(tokenParam);
    }
  }, []);

  const verify = async (tok: string) => {
    if (!tok.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await api.get(`/api/v1/auth/verify-email?token=${tok.trim()}`);
      setSuccess(true);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Invalid or expired email verification link.');
    } finally {
      setLoading(false);
    }
  };

  const handleManualSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    verify(tokenInput);
  };

  return (
    <div className="min-h-screen bg-[#07090e] text-slate-100 flex items-center justify-center p-6 relative overflow-hidden font-sans">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-cyan-500/10 blur-[130px] pointer-events-none" />

      <div className="w-full max-w-md space-y-6 relative z-10">
        <div className="text-center space-y-2">
          <div
            onClick={() => setActiveTab('landing')}
            className="inline-flex items-center justify-center cursor-pointer mb-1"
          >
            <SpecraLogo size="lg" layout="stacked" showTagline />
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Email Verification</h2>
          <p className="text-xs text-slate-400">Verifying your SPECra workspace email address.</p>
        </div>

        <div className="specra-panel rounded-3xl p-8 border border-slate-800 space-y-5">
          {loading ? (
            <div className="text-center space-y-3 py-6">
              <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto" />
              <p className="text-xs text-slate-400">Verifying your token...</p>
            </div>
          ) : success ? (
            <div className="text-center space-y-4 py-4 animate-fadeIn">
              <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center mx-auto border border-emerald-500/20">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-white">Email verified</h3>
              <p className="text-xs text-slate-300">
                Your email address has been confirmed. Your workspace is now fully verified.
              </p>
              <button
                onClick={() => setActiveTab('dashboard')}
                className="w-full py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs transition-colors cursor-pointer"
              >
                Go to Dashboard
              </button>
            </div>
          ) : error ? (
            <div className="text-center space-y-4 py-4 animate-fadeIn">
              <div className="w-12 h-12 rounded-2xl bg-rose-500/10 text-rose-400 flex items-center justify-center mx-auto border border-rose-500/20">
                <AlertCircle className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-white">Verification Failed</h3>
              <p className="text-xs text-slate-300">{error}</p>
              <button
                onClick={() => setActiveTab('login')}
                className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs transition-colors cursor-pointer"
              >
                Back to Sign in
              </button>
            </div>
          ) : (
            <form onSubmit={handleManualSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300">Verification Token</label>
                <input
                  type="text"
                  required
                  value={tokenInput}
                  onChange={(e) => setTokenInput(e.target.value)}
                  placeholder="Paste verification token from email"
                  className="specra-input w-full px-4 py-2.5 rounded-xl text-xs"
                />
              </div>

              <button
                type="submit"
                className="w-full py-3 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs transition-all shadow-lg shadow-cyan-500/20 flex items-center justify-center gap-2 cursor-pointer mt-2"
              >
                <span>Verify Email</span>
                <ShieldCheck className="w-3.5 h-3.5" />
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};
