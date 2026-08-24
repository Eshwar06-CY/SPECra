import React, { useState } from 'react';
import { ArrowRight, Mail, ArrowLeft, CheckCircle2, AlertCircle } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { SpecraLogo } from '../components/ui/SpecraLogo';
import { api } from '../api/client';

export const ForgotPassword: React.FC = () => {
  const { setActiveTab } = useApp();
  const [email, setEmail] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [submitted, setSubmitted] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await api.post('/api/v1/auth/forgot-password', { email });
      setSubmitted(true);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Unable to request password reset. Please try again.');
    } finally {
      setLoading(false);
    }
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
          <h2 className="text-2xl font-bold text-white tracking-tight">Reset password</h2>
          <p className="text-xs text-slate-400">Enter your work email to receive password reset instructions.</p>
        </div>

        <div className="specra-panel rounded-3xl p-8 border border-slate-800 space-y-5">
          {submitted ? (
            <div className="text-center space-y-4 py-4 animate-fadeIn">
              <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center mx-auto border border-emerald-500/20">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-white">Check your email</h3>
              <p className="text-xs text-slate-300">
                If an account exists for <strong className="text-white">{email}</strong>, you will receive a reset link shortly.
              </p>
              <button
                onClick={() => setActiveTab('login')}
                className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs transition-colors"
              >
                Back to Sign in
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300">Work Email</label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@company.com"
                    className="specra-input w-full pl-10 pr-4 py-2.5 rounded-xl text-xs"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs transition-all shadow-lg shadow-cyan-500/20 flex items-center justify-center gap-2 cursor-pointer mt-2"
              >
                <span>{loading ? 'Sending...' : 'Send instructions'}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </form>
          )}

          <div className="text-center pt-2 border-t border-slate-800">
            <button
              onClick={() => setActiveTab('login')}
              className="text-xs text-slate-400 hover:text-white flex items-center justify-center gap-1.5 mx-auto transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Sign in</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
