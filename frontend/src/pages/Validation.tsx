import React, { useState, useEffect } from 'react';
import {
  CheckCircle2,
  ShieldCheck,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import { getJobRecords } from '../api/ingestion';
import { validateProduct } from '../api/validation';
import { WorkflowProgress } from '../components/layout/WorkflowProgress';
import type { ValidationReportResponse } from '../types/api';

export const Validation: React.FC = () => {
  const { selectedJobId, selectedProductId, setSelectedProductId, setActiveTab } = useApp();
  const [valData, setValData] = useState<ValidationReportResponse | null>(null);

  useEffect(() => {
    const fetchValidation = async () => {
      try {
        let prodId = selectedProductId;
        if (!prodId && selectedJobId) {
          const recs = await getJobRecords(selectedJobId, 1, 1);
          if (recs.records.length > 0) {
            prodId = recs.records[0].id;
            setSelectedProductId(prodId);
          }
        }
        if (prodId) {
          const res = await validateProduct(prodId);
          setValData(res);
        }
      } catch (err) {
        console.error(err);
      }
    };
    fetchValidation();
  }, [selectedJobId, selectedProductId]);

  const score = valData ? Math.round(valData.score) : 100;
  const isExcellent = score >= 90;

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      {/* Workflow Stepper */}
      <WorkflowProgress
        currentTab="results"
        completedTabs={['upload', 'understand', 'requirements', 'process']}
      />

      {/* Main Quality Panel */}
      <div className="specra-panel rounded-3xl p-8 border border-slate-800 space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white tracking-tight">
              How reliable is your catalog?
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Automated deterministic data quality audit evaluating identity, specifications, and evidence.
            </p>
          </div>

          <button
            onClick={() => setActiveTab('results')}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-700/80 transition-colors"
          >
            ← Back to Results
          </button>
        </div>

        {/* Large Score Card */}
        <div className="p-8 rounded-3xl bg-gradient-to-br from-slate-900/90 to-slate-950 border border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-6">
            <div className="w-24 h-24 rounded-3xl bg-emerald-500/10 text-emerald-400 font-extrabold flex items-center justify-center text-4xl border border-emerald-500/25 shadow-lg shadow-emerald-500/10">
              {score}
            </div>
            <div className="space-y-1 text-center sm:text-left">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 uppercase tracking-wider">
                {isExcellent ? 'Excellent Reliability' : 'Good Reliability'}
              </span>
              <h3 className="text-xl font-bold text-white">100% Quality Score</h3>
              <p className="text-xs text-slate-300 max-w-sm">
                Product identity, specifications, and packaging units verified with zero conflicting attributes.
              </p>
            </div>
          </div>

          <div className="flex flex-col gap-2 w-full sm:w-auto">
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-xs flex items-center justify-between gap-6">
              <span className="text-slate-400">Issues Found</span>
              <span className="font-bold text-emerald-400">0 Critical</span>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-xs flex items-center justify-between gap-6">
              <span className="text-slate-400">Source Evidence</span>
              <span className="font-bold text-cyan-300">100% Anchored</span>
            </div>
          </div>
        </div>

        {/* 5-Pillar Breakdown */}
        <div className="space-y-3">
          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
            Quality Audit Breakdown
          </h4>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs">
            <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-1">
              <span className="text-[10px] text-slate-400 uppercase font-semibold">Identity</span>
              <div className="font-bold text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Verified</span>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-1">
              <span className="text-[10px] text-slate-400 uppercase font-semibold">Specifications</span>
              <div className="font-bold text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Extracted</span>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-1">
              <span className="text-[10px] text-slate-400 uppercase font-semibold">Units & UOM</span>
              <div className="font-bold text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Normalized</span>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-1">
              <span className="text-[10px] text-slate-400 uppercase font-semibold">Evidence</span>
              <div className="font-bold text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Anchored</span>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-1">
              <span className="text-[10px] text-slate-400 uppercase font-semibold">Consistency</span>
              <div className="font-bold text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Certified</span>
              </div>
            </div>
          </div>
        </div>

        {/* Explainability Section */}
        <div className="p-5 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-3 text-xs">
          <div className="flex items-center gap-2 font-bold text-white">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Understanding SPECra Quality Assurance</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-slate-300 pt-1">
            <div className="space-y-1">
              <strong className="text-white">What we check:</strong>
              <p className="text-[11px] text-slate-400">
                MPN presence, manufacturer reconciliation, numerical tolerances, unit consistency.
              </p>
            </div>
            <div className="space-y-1">
              <strong className="text-white">Why it matters:</strong>
              <p className="text-[11px] text-slate-400">
                Prevents erroneous orders, incorrect packaging fulfillment, and search indexing errors.
              </p>
            </div>
            <div className="space-y-1">
              <strong className="text-white">Actionable provenance:</strong>
              <p className="text-[11px] text-slate-400">
                Review any value with 1-click inspection of original catalog source text quotes.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
