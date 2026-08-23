import React, { useState } from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ShieldAlert,
  Search,
} from 'lucide-react';
import type { ValidationReport } from '../types';
import { validateProduct } from '../services/api';

interface ValidationAuditViewProps {
  initialProductId?: string;
}

export const ValidationAuditView: React.FC<ValidationAuditViewProps> = ({
  initialProductId = 'b17feefb-5796-4b91-b487-dd6eb9bad9f7',
}) => {
  const [productIdInput, setProductIdInput] = useState(initialProductId);
  const [validationReport, setValidationReport] = useState<ValidationReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleRunValidation = async () => {
    const targetId = productIdInput.trim();
    if (!targetId) return;

    setLoading(true);
    setErrorMsg(null);

    try {
      const data = await validateProduct(targetId);
      setValidationReport(data);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to run deterministic validation.');
      setValidationReport(null);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    if (status === 'passed') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
          <CheckCircle2 className="w-3.5 h-3.5" />
          PASSED
        </span>
      );
    }
    if (status === 'warning') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-400 border border-amber-500/30">
          <AlertTriangle className="w-3.5 h-3.5" />
          WARNING
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/15 text-rose-400 border border-rose-500/30">
        <XCircle className="w-3.5 h-3.5" />
        FAILED
      </span>
    );
  };

  return (
    <div className="space-y-8">
      {/* Top Search & Trigger Bar */}
      <div className="glass-panel rounded-2xl p-6 border border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex-1 w-full flex items-center gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={productIdInput}
              onChange={(e) => setProductIdInput(e.target.value)}
              placeholder="Enter Product UUID to audit (e.g. b17feefb-5796-4b91-b487-dd6eb9bad9f7)..."
              className="glass-input w-full pl-10 pr-4 py-2.5 rounded-xl text-sm font-mono text-slate-200 placeholder:text-slate-500"
            />
          </div>
          <button
            onClick={handleRunValidation}
            disabled={loading}
            className="px-5 py-2.5 rounded-xl text-sm font-semibold bg-emerald-500 hover:bg-emerald-400 text-slate-950 transition-all shadow-md shadow-emerald-500/20 disabled:opacity-50 flex items-center gap-2"
          >
            <ShieldAlert className="w-4 h-4" />
            {loading ? 'Auditing...' : 'Run Deterministic Audit'}
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {validationReport && (
        <div className="space-y-6">
          {/* Quality Scorecard Banner */}
          <div className="glass-panel rounded-2xl p-8 border border-slate-800 flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <h2 className="text-2xl font-bold text-white tracking-tight">
                  Product Quality & Validation Scorecard
                </h2>
                {getStatusBadge(validationReport.status)}
              </div>
              <p className="text-xs text-slate-400">
                Deterministic rule evaluation over identity completeness, unit sanity, and evidence links.
              </p>
            </div>

            {/* Score Pill Breakdown */}
            <div className="flex items-center gap-4 bg-slate-900/80 p-4 rounded-2xl border border-slate-800">
              <div className="text-center px-4 border-r border-slate-800">
                <div
                  className={`text-3xl font-extrabold ${
                    validationReport.score >= 90
                      ? 'text-emerald-400'
                      : validationReport.score >= 70
                      ? 'text-amber-400'
                      : 'text-rose-400'
                  }`}
                >
                  {validationReport.score.toFixed(0)}
                  <span className="text-sm font-normal text-slate-500">/100</span>
                </div>
                <div className="text-[11px] uppercase tracking-wider text-slate-500 mt-0.5">
                  Quality Score
                </div>
              </div>

              <div className="flex items-center gap-4 px-2">
                <div className="text-center">
                  <div className="text-lg font-bold text-rose-400">{validationReport.errors}</div>
                  <div className="text-[10px] text-slate-500">Errors</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold text-amber-400">{validationReport.warnings}</div>
                  <div className="text-[10px] text-slate-500">Warnings</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold text-cyan-400">{validationReport.info}</div>
                  <div className="text-[10px] text-slate-500">Info</div>
                </div>
              </div>
            </div>
          </div>

          {/* Detailed Audit Findings */}
          <div className="glass-panel rounded-2xl p-6 border border-slate-800">
            <h3 className="text-base font-bold text-white mb-4">Audit Findings</h3>
            {validationReport.results.length === 0 ? (
              <div className="text-center py-12 text-slate-400 space-y-2">
                <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto" />
                <div className="text-sm font-semibold text-white">Zero Validation Anomalies</div>
                <div className="text-xs text-slate-500">
                  All canonical identity, physical units, dimensions, and evidence anchors are 100% verified.
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                {validationReport.results.map((res, idx) => (
                  <div
                    key={idx}
                    className={`rounded-xl p-4 border flex flex-col md:flex-row items-start md:items-center justify-between gap-4 ${
                      res.severity === 'ERROR'
                        ? 'bg-rose-500/10 border-rose-500/20'
                        : res.severity === 'WARNING'
                        ? 'bg-amber-500/10 border-amber-500/20'
                        : 'bg-cyan-500/10 border-cyan-500/20'
                    }`}
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-white text-sm">{res.field}</span>
                        <span
                          className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${
                            res.severity === 'ERROR'
                              ? 'bg-rose-500/20 text-rose-300 border-rose-500/30'
                              : res.severity === 'WARNING'
                              ? 'bg-amber-500/20 text-amber-300 border-amber-500/30'
                              : 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30'
                          }`}
                        >
                          {res.validation_type}
                        </span>
                      </div>
                      <div className="text-xs text-slate-300">{res.message}</div>
                    </div>

                    {res.expected_condition && (
                      <div className="text-xs text-slate-400 bg-slate-950/60 px-3 py-1.5 rounded-lg border border-slate-800">
                        <span className="text-slate-500">Requirement:</span> {res.expected_condition}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
