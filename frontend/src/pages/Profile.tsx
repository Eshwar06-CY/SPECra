import React, { useState, useEffect } from 'react';
import {
  User,
  Building,
  Mail,
  Key,
  LogOut,
  CheckCircle2,
  Lock,
  Smartphone,
  Sparkles,
  AlertTriangle,
  Trash2,
  RefreshCw,
  AlertCircle,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useApp } from '../context/AppContext';
import { api } from '../api/client';

interface SessionItem {
  id: string;
  created_at: string;
  expires_at: string;
  is_current: boolean;
}

export const Profile: React.FC = () => {
  const { user, logout, updateProfile } = useAuth();
  const { setActiveTab } = useApp();
  const [name, setName] = useState(user?.name || 'Alex Rivera');
  const [org, setOrg] = useState(user?.organization || 'Apex Industrial Supply Co.');
  const [email] = useState(user?.email || 'alex.rivera@industrialtech.io');
  const [savedSuccess, setSavedSuccess] = useState(false);

  // Password change state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [passwordMsg, setPasswordMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Sessions state
  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(false);

  // Account deletion state
  const [deletePassword, setDeletePassword] = useState('');
  const [confirmPhrase, setConfirmPhrase] = useState('');
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    setSessionsLoading(true);
    try {
      const res = await api.get('/api/v1/auth/sessions');
      if (Array.isArray(res.data)) {
        setSessions(res.data);
      }
    } catch {
      // Offline fallback
    } finally {
      setSessionsLoading(false);
    }
  };

  const handleRevokeSession = async (sessionId: string) => {
    try {
      await api.delete(`/api/v1/auth/sessions/${sessionId}`);
      fetchSessions();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to revoke session.');
    }
  };

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    updateProfile({ name, organization: org });
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordMsg(null);

    if (newPassword !== confirmPassword) {
      setPasswordMsg({ type: 'error', text: 'New passwords do not match.' });
      return;
    }
    if (newPassword.length < 8) {
      setPasswordMsg({ type: 'error', text: 'New password must be at least 8 characters long.' });
      return;
    }

    setPasswordLoading(true);
    try {
      await api.post('/api/v1/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setPasswordMsg({ type: 'success', text: 'Your password has been changed successfully.' });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      fetchSessions();
    } catch (err: any) {
      setPasswordMsg({
        type: 'error',
        text: err?.response?.data?.detail || 'Failed to change password. Please verify current password.',
      });
    } finally {
      setPasswordLoading(false);
    }
  };

  const handleDeleteAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    setDeleteError(null);

    if (confirmPhrase !== 'DELETE MY ACCOUNT') {
      setDeleteError('Please type DELETE MY ACCOUNT exactly to confirm.');
      return;
    }

    setDeleteLoading(true);
    try {
      await api.post('/api/v1/auth/delete-account', {
        password: deletePassword,
        confirm_text: confirmPhrase,
      });
      await logout();
      setActiveTab('landing');
    } catch (err: any) {
      setDeleteError(err?.response?.data?.detail || 'Failed to delete account. Please verify your password.');
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleLogout = async () => {
    await logout();
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
          className="px-4 py-2 rounded-xl text-xs font-semibold bg-rose-500/10 text-rose-300 hover:bg-rose-500/20 border border-rose-500/20 flex items-center gap-1.5 transition-colors cursor-pointer"
        >
          <LogOut className="w-3.5 h-3.5" />
          <span>Sign out</span>
        </button>
      </div>

      {/* 1. Profile Information Form */}
      <div className="specra-panel rounded-3xl p-8 border border-slate-800 space-y-6">
        <div className="flex items-center gap-4 border-b border-slate-800 pb-6">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center text-xl font-bold text-white shadow-lg shadow-cyan-500/20">
            {name.charAt(0).toUpperCase()}
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">{name}</h3>
            <p className="text-xs text-slate-400 font-mono mt-0.5">{email}</p>
            <div className="flex items-center gap-2 mt-2">
              <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 text-[10px] font-semibold">
                <Sparkles className="w-3 h-3" />
                <span>{user?.role || 'Workspace Owner'}</span>
              </div>
              <div className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] font-semibold">
                <CheckCircle2 className="w-3 h-3" />
                <span>Verified Account</span>
              </div>
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
              <span className="text-[11px] text-slate-500">Workspace data is isolated to your organization.</span>
            )}
            <button
              type="submit"
              className="px-6 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs transition-all shadow-md shadow-cyan-500/20 cursor-pointer"
            >
              Save Changes
            </button>
          </div>
        </form>
      </div>

      {/* 2. Security & Change Password Panel */}
      <div className="specra-panel rounded-3xl p-8 border border-slate-800 space-y-6">
        <div className="flex items-center gap-2 text-sm font-bold text-white border-b border-slate-800 pb-3">
          <Key className="w-4 h-4 text-cyan-400" />
          <span>Change Password</span>
        </div>

        <form onSubmit={handleChangePassword} className="space-y-4 max-w-md">
          {passwordMsg && (
            <div
              className={`p-3 rounded-xl text-xs flex items-center gap-2 ${
                passwordMsg.type === 'success'
                  ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-300'
                  : 'bg-rose-500/10 border border-rose-500/20 text-rose-300'
              }`}
            >
              {passwordMsg.type === 'success' ? (
                <CheckCircle2 className="w-4 h-4 shrink-0" />
              ) : (
                <AlertCircle className="w-4 h-4 shrink-0" />
              )}
              <span>{passwordMsg.text}</span>
            </div>
          )}

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300">Current Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="password"
                required
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                placeholder="Enter current password"
                className="specra-input w-full pl-10 pr-4 py-2.5 rounded-xl text-xs"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300">New Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="password"
                required
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="At least 8 characters"
                className="specra-input w-full pl-10 pr-4 py-2.5 rounded-xl text-xs"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300">Confirm New Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Repeat new password"
                className="specra-input w-full pl-10 pr-4 py-2.5 rounded-xl text-xs"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={passwordLoading}
            className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs transition-colors cursor-pointer"
          >
            {passwordLoading ? 'Updating...' : 'Update Password'}
          </button>
        </form>
      </div>

      {/* 3. Active Sessions */}
      <div className="specra-panel rounded-3xl p-8 border border-slate-800 space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2 text-sm font-bold text-white">
            <Smartphone className="w-4 h-4 text-emerald-400" />
            <span>Active Login Sessions</span>
          </div>
          <button
            onClick={fetchSessions}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
            title="Refresh sessions"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="space-y-3">
          {sessions.length > 0 ? (
            sessions.map((sess) => (
              <div
                key={sess.id}
                className="flex items-center justify-between p-4 rounded-2xl bg-slate-950/60 border border-slate-800"
              >
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-300">
                    <Smartphone className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-white font-mono">{sess.id.slice(0, 8)}...</span>
                      {sess.is_current && (
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold">
                          Current Session
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      Created: {new Date(sess.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>

                {!sess.is_current && (
                  <button
                    onClick={() => handleRevokeSession(sess.id)}
                    className="px-3 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 text-rose-300 text-xs font-semibold transition-colors cursor-pointer"
                  >
                    Revoke
                  </button>
                )}
              </div>
            ))
          ) : (
            <div className="p-4 rounded-2xl bg-slate-950/40 border border-slate-800/80 text-xs text-slate-400">
              {sessionsLoading ? 'Loading sessions...' : '1 Active Session on current browser.'}
            </div>
          )}
        </div>
      </div>

      {/* 4. Danger Zone — Account Deletion */}
      <div className="specra-panel rounded-3xl p-8 border border-rose-950/40 bg-rose-950/10 space-y-6">
        <div className="flex items-center gap-2 text-sm font-bold text-rose-400 border-b border-rose-900/30 pb-3">
          <AlertTriangle className="w-4 h-4" />
          <span>Danger Zone — Delete Account</span>
        </div>

        <p className="text-xs text-slate-400">
          Permanently delete your account and all associated workspace catalog data. This action is irreversible.
        </p>

        <form onSubmit={handleDeleteAccount} className="space-y-4 max-w-md">
          {deleteError && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{deleteError}</span>
            </div>
          )}

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300">Account Password</label>
            <input
              type="password"
              required
              value={deletePassword}
              onChange={(e) => setDeletePassword(e.target.value)}
              placeholder="Confirm your password"
              className="specra-input w-full px-4 py-2.5 rounded-xl text-xs"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300">
              Type <strong className="text-rose-400">DELETE MY ACCOUNT</strong> to confirm
            </label>
            <input
              type="text"
              required
              value={confirmPhrase}
              onChange={(e) => setConfirmPhrase(e.target.value)}
              placeholder="DELETE MY ACCOUNT"
              className="specra-input w-full px-4 py-2.5 rounded-xl text-xs"
            />
          </div>

          <button
            type="submit"
            disabled={deleteLoading}
            className="px-5 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs transition-colors flex items-center gap-2 cursor-pointer shadow-lg shadow-rose-600/20"
          >
            <Trash2 className="w-4 h-4" />
            <span>{deleteLoading ? 'Deleting...' : 'Permanently Delete Account'}</span>
          </button>
        </form>
      </div>
    </div>
  );
};

