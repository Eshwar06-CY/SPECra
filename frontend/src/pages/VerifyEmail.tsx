import React, { useState, useEffect } from 'react';
import { CheckCircle2, AlertCircle, ShieldCheck, Mail, Send, ArrowLeft } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { SpecraLogo } from '../components/ui/SpecraLogo';
import { api } from '../api/client';

export const VerifyEmail: React.FC = () => {
  const { setActiveTab } = useApp();
  const [tokenInput, setTokenInput] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [success, setSuccess] = useState<boolean>(false);
  const [successMessage, setSuccessMessage] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  // Resend Verification State
  const [showResend, setShowResend] = useState<boolean>(false);
  const [resendEmail, setResendEmail] = useState<string>('');
  const [resendLoading, setResendLoading] = useState<boolean>(false);
  const [resendStatus, setResendStatus] = useState<string | null>(null);

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
      const res = await api.post('/api/v1/auth/verify-email', { token: tok.trim() });
      setSuccess(true);
      setSuccessMessage(res.data?.message || 'Your email address has been verified successfully.');
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

  const handleResendSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resendEmail.trim()) return;
    setResendLoading(true);
    setResendStatus(null);
    try {
      const res = await api.post('/api/v1/auth/resend-verification', { email: resendEmail.trim() });
      setResendStatus(res.data?.message || 'If the account requires verification, a new verification email has been sent.');
    } catch (err: any) {
      setResendStatus(err?.response?.data?.detail || 'Unable to dispatch verification email at this time.');
    } finally {
      setResendLoading(false);
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
          <h2 className="text-2xl font-bold text-white tracking-tight">Email Verification</h2>
          <p className="text-xs text-slate-400">Secure your SPECra workspace with cryptographic verification.</p>
        </div>

        <div className="specra-panel rounded-3xl p-8 border border-slate-800 space-y-5">
          {loading ? (
            <div className="text-center space-y-3 py-6">
              <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto" />
              <p className="text-xs text-slate-400">Verifying cryptographic token...</p>
            </div>
          ) : success ? (
            <div className="text-center space-y-4 py-4 animate-fadeIn">
              <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center mx-auto border border-emerald-500/20">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-white">Email Verified Successfully</h3>
              <p className="text-xs text-slate-300">{successMessage}</p>
              <div className="pt-2 flex flex-col gap-2">
                <button
                  onClick={() => setActiveTab('dashboard')}
                  className="w-full py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs transition-colors cursor-pointer"
                >
                  Continue to Dashboard
                </button>
                <button
                  onClick={() => setActiveTab('login')}
                  className="w-full py-2 rounded-xl bg-slate-800/60 hover:bg-slate-800 text-slate-300 font-medium text-xs transition-colors cursor-pointer"
                >
                  Sign In with Credentials
                </button>
              </div>
            </div>
          ) : error ? (
            <div className="text-center space-y-4 py-2 animate-fadeIn">
              <div className="w-12 h-12 rounded-2xl bg-rose-500/10 text-rose-400 flex items-center justify-center mx-auto border border-rose-500/20">
                <AlertCircle className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-white">Verification Link Expired or Invalid</h3>
              <p className="text-xs text-slate-300">{error}</p>

              {!showResend ? (
                <div className="pt-2 flex flex-col gap-2">
                  <button
                    onClick={() => setShowResend(true)}
                    className="w-full py-2.5 rounded-xl bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 text-cyan-400 font-semibold text-xs transition-colors cursor-pointer flex items-center justify-center gap-2"
                  >
                    <Mail className="w-3.5 h-3.5" />
                    <span>Resend Verification Email</span>
                  </button>
                  <button
                    onClick={() => setActiveTab('login')}
                    className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs transition-colors cursor-pointer"
                  >
                    Back to Sign In
                  </button>
                </div>
              ) : (
                <form onSubmit={handleResendSubmit} className="space-y-3 pt-2 text-left animate-fadeIn">
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-slate-300">Account Email Address</label>
                    <input
                      type="email"
                      required
                      value={resendEmail}
                      onChange={(e) => setResendEmail(e.target.value)}
                      placeholder="name@company.com"
                      className="specra-input w-full px-4 py-2.5 rounded-xl text-xs"
                    />
                  </div>

                  {resendStatus && (
                    <div className="p-3 rounded-xl bg-cyan-950/40 border border-cyan-500/30 text-cyan-300 text-xs">
                      {resendStatus}
                    </div>
                  )}

                  <div className="flex gap-2 pt-1">
                    <button
                      type="button"
                      onClick={() => setShowResend(false)}
                      className="w-1/3 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium cursor-pointer"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={resendLoading}
                      className="w-2/3 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                    >
                      {resendLoading ? (
                        <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                      ) : (
                        <>
                          <span>Send Link</span>
                          <Send className="w-3 h-3" />
                        </>
                      )}
                    </button>
                  </div>
                </form>
              )}
            </div>
          ) : (
            <div className="space-y-4">
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

              <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs">
                <button
                  onClick={() => setShowResend(true)}
                  className="text-cyan-400 hover:text-cyan-300 transition-colors cursor-pointer"
                >
                  Need a new verification link?
                </button>
                <button
                  onClick={() => setActiveTab('login')}
                  className="text-slate-400 hover:text-slate-200 transition-colors cursor-pointer flex items-center gap-1"
                >
                  <ArrowLeft className="w-3 h-3" />
                  <span>Sign In</span>
                </button>
              </div>

              {showResend && (
                <form onSubmit={handleResendSubmit} className="space-y-3 pt-3 border-t border-slate-800 text-left animate-fadeIn">
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-slate-300">Account Email Address</label>
                    <input
                      type="email"
                      required
                      value={resendEmail}
                      onChange={(e) => setResendEmail(e.target.value)}
                      placeholder="name@company.com"
                      className="specra-input w-full px-4 py-2.5 rounded-xl text-xs"
                    />
                  </div>

                  {resendStatus && (
                    <div className="p-3 rounded-xl bg-cyan-950/40 border border-cyan-500/30 text-cyan-300 text-xs">
                      {resendStatus}
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={resendLoading}
                    className="w-full py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                  >
                    {resendLoading ? (
                      <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <>
                        <span>Resend Verification Email</span>
                        <Send className="w-3 h-3" />
                      </>
                    )}
                  </button>
                </form>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
