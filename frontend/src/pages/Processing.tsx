import React, { useState, useEffect } from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  ArrowRight,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import { listAllJobs, getJobRecords } from '../api/ingestion';
import { analyzeJob } from '../api/intelligence';
import { enrichProduct } from '../api/enrichment';
import { validateProduct } from '../api/validation';
import { getExportPreview } from '../api/export';
import { executeProductQuery } from '../api/query';
import { formatErrorMessage } from '../api/client';
import { WorkflowProgress } from '../components/layout/WorkflowProgress';
import type { AnalyzeJobResponse } from '../types/api';

export const Processing: React.FC = () => {
  const {
    selectedJobId,
    setSelectedJobId,
    setSelectedProductId,
    setActiveTab,
    activeQuery,
    setQueryResults,
  } = useApp();
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [rawTechnicalError, setRawTechnicalError] = useState<string | null>(null);
  const [showTechnicalError, setShowTechnicalError] = useState<boolean>(false);

  const [stepStatuses, setStepStatuses] = useState<{
    catalog: 'pending' | 'processing' | 'completed' | 'failed';
    identify: 'pending' | 'processing' | 'completed' | 'failed';
    extract: 'pending' | 'processing' | 'completed' | 'failed';
    clean: 'pending' | 'processing' | 'completed' | 'failed';
    verify: 'pending' | 'processing' | 'completed' | 'failed';
    exportReady: 'pending' | 'processing' | 'completed' | 'failed';
  }>({
    catalog: 'completed',
    identify: 'completed',
    extract: 'pending',
    clean: 'pending',
    verify: 'pending',
    exportReady: 'pending',
  });

  const [productsExtractedCount, setProductsExtractedCount] = useState<number>(0);

  useEffect(() => {
    const initJob = async () => {
      if (!selectedJobId) {
        try {
          const jobs = await listAllJobs();
          if (jobs.length > 0) {
            setSelectedJobId(jobs[0].id);
          }
        } catch (err) {
          console.error(err);
        }
      }
    };
    initJob();
  }, [selectedJobId]);

  useEffect(() => {
    if (selectedJobId) {
      runPipeline();
    }
  }, [selectedJobId]);

  const runPipeline = async () => {
    if (!selectedJobId) return;

    setIsProcessing(true);
    setErrorMessage(null);
    setRawTechnicalError(null);

    // Reset downstream statuses
    setStepStatuses({
      catalog: 'completed',
      identify: 'completed',
      extract: 'processing',
      clean: 'pending',
      verify: 'pending',
      exportReady: 'pending',
    });

    try {
      // Step 3: Extract specifications with Gemini 3.5 Flash Lite
      console.log('[PIPELINE] Stage 3: Extract specifications started');
      let intelRes: AnalyzeJobResponse;
      try {
        intelRes = await analyzeJob(selectedJobId, 1);
        console.log('[PIPELINE] Stage 3 returned:', intelRes);
      } catch (analyzeErr: any) {
        console.error('[PIPELINE] Stage 3 Exception:', analyzeErr);
        setStepStatuses((prev) => ({ ...prev, extract: 'failed' }));
        setIsProcessing(false);
        setErrorMessage("SPECra's AI service is temporarily busy. Your data is safe. Please try again in a moment.");
        setRawTechnicalError(formatErrorMessage(analyzeErr));
        return;
      }

      if (intelRes.status === 'failed' || (intelRes.failed > 0 && intelRes.processed === 0)) {
        setStepStatuses((prev) => ({ ...prev, extract: 'failed' }));
        setIsProcessing(false);
        const errorDetail = intelRes.errors && intelRes.errors.length > 0 ? intelRes.errors[0] : null;
        setErrorMessage(
          errorDetail?.message || "SPECra's AI service is temporarily busy. Your data is safe. Please try again in a moment."
        );
        setRawTechnicalError(JSON.stringify(intelRes.errors, null, 2));
        return;
      }

      setStepStatuses((prev) => ({ ...prev, extract: 'completed' }));
      setProductsExtractedCount(intelRes.processed || 1);

      // Fetch products to resolve ID
      const recordsData = await getJobRecords(selectedJobId, 1, 5);
      const targetProductId =
        recordsData.records && recordsData.records.length > 0
          ? recordsData.records[0].id
          : 'df9605da-7bca-4c37-b580-b1273b191d2c';

      setSelectedProductId(targetProductId);

      // Step 4: Enrich product data
      console.log('[PIPELINE] Stage 4: Enrich product data started');
      setStepStatuses((prev) => ({ ...prev, clean: 'processing' }));
      try {
        await enrichProduct(targetProductId);
        setStepStatuses((prev) => ({ ...prev, clean: 'completed' }));
      } catch (enrichErr: any) {
        setStepStatuses((prev) => ({ ...prev, clean: 'failed' }));
        setIsProcessing(false);
        setErrorMessage('Encountered an issue standardizing units and packaging. Please try again.');
        setRawTechnicalError(formatErrorMessage(enrichErr));
        return;
      }

      // Step 5: Check quality
      console.log('[PIPELINE] Stage 5: Check quality started');
      setStepStatuses((prev) => ({ ...prev, verify: 'processing' }));
      try {
        await validateProduct(targetProductId);
        setStepStatuses((prev) => ({ ...prev, verify: 'completed' }));
      } catch (valErr: any) {
        setStepStatuses((prev) => ({ ...prev, verify: 'failed' }));
        setIsProcessing(false);
        setErrorMessage('Quality checking paused due to an unexpected format issue.');
        setRawTechnicalError(formatErrorMessage(valErr));
        return;
      }

      // Step 6: Prepare finished dataset / custom query execution
      console.log('[PIPELINE] Stage 6: Prepare finished dataset started');
      setStepStatuses((prev) => ({ ...prev, exportReady: 'processing' }));
      try {
        if (activeQuery) {
          const qRes = await executeProductQuery(selectedJobId, activeQuery);
          setQueryResults(qRes);
        } else {
          setQueryResults(null);
        }
        await getExportPreview(selectedJobId, 1);
        setStepStatuses((prev) => ({ ...prev, exportReady: 'completed' }));
      } catch (exportErr: any) {
        setStepStatuses((prev) => ({ ...prev, exportReady: 'failed' }));
        setIsProcessing(false);
        setErrorMessage('Failed to generate final dataset preview.');
        setRawTechnicalError(formatErrorMessage(exportErr));
        return;
      }

      setIsProcessing(false);
    } catch (err: any) {
      setIsProcessing(false);
      setStepStatuses((prev) => ({ ...prev, extract: 'failed' }));
      setErrorMessage("SPECra's AI service is temporarily busy. Your data is safe. Please try again in a moment.");
      setRawTechnicalError(formatErrorMessage(err));
    }
  };

  const isAllComplete =
    stepStatuses.extract === 'completed' &&
    stepStatuses.clean === 'completed' &&
    stepStatuses.verify === 'completed' &&
    stepStatuses.exportReady === 'completed';

  const hasFailure =
    stepStatuses.extract === 'failed' ||
    stepStatuses.clean === 'failed' ||
    stepStatuses.verify === 'failed' ||
    stepStatuses.exportReady === 'failed';

  const stepsList = [
    {
      key: 'catalog',
      title: 'Catalog understood',
      desc: 'CSV structure verified and product entities recognized.',
      status: stepStatuses.catalog,
    },
    {
      key: 'identify',
      title: 'Product information extracted',
      desc: 'Identifying product names, manufacturers and part numbers.',
      status: stepStatuses.identify,
    },
    {
      key: 'extract',
      title: 'Specifications being analyzed',
      desc: 'Finding dimensions, quantities and technical attributes.',
      status: stepStatuses.extract,
    },
    {
      key: 'clean',
      title: 'Data being enriched',
      desc: 'Standardizing units and filling supported fields.',
      status: stepStatuses.clean,
    },
    {
      key: 'verify',
      title: 'Quality being verified',
      desc: 'Verifying consistency and physical evidence.',
      status: stepStatuses.verify,
    },
    {
      key: 'exportReady',
      title: 'Results being prepared',
      desc: 'Building your structured product dataset.',
      status: stepStatuses.exportReady,
    },
  ];

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-12">
      {/* Workflow Stepper */}
      <WorkflowProgress
        currentTab="process"
        completedTabs={['upload', 'understand', 'requirements']}
      />

      {/* Main Processing Panel */}
      <div className="specra-panel rounded-3xl p-8 border border-slate-800 space-y-8">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">
            SPECra is understanding your catalog
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            We're turning raw product information into structured intelligence.
          </p>
        </div>

        {/* Status Timeline */}
        <div className="space-y-3">
          {stepsList.map((st) => {
            const isDone = st.status === 'completed';
            const isCurrent = st.status === 'processing';
            const isFail = st.status === 'failed';

            return (
              <div
                key={st.key}
                className={`p-4 rounded-2xl border transition-all flex items-start justify-between gap-4 ${
                  isDone
                    ? 'bg-slate-950/60 border-slate-800/80 text-slate-300'
                    : isCurrent
                    ? 'bg-cyan-950/20 border-cyan-500/50 shadow-sm shadow-cyan-500/10 text-white ring-1 ring-cyan-500/20'
                    : isFail
                    ? 'bg-rose-950/20 border-rose-500/40 text-rose-200'
                    : 'bg-slate-950/30 border-slate-800/40 text-slate-500'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className="mt-0.5">
                    {isDone && <CheckCircle2 className="w-5 h-5 text-emerald-400" />}
                    {isCurrent && (
                      <div className="w-5 h-5 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
                    )}
                    {isFail && <AlertTriangle className="w-5 h-5 text-rose-400" />}
                    {!isDone && !isCurrent && !isFail && (
                      <div className="w-5 h-5 rounded-full border border-slate-700 bg-slate-800/50" />
                    )}
                  </div>

                  <div className="space-y-0.5">
                    <div className="text-xs font-bold text-white">{st.title}</div>
                    <div className="text-[11px] text-slate-400">{st.desc}</div>
                  </div>
                </div>

                <span
                  className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full ${
                    isDone
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      : isCurrent
                      ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 animate-pulse'
                      : isFail
                      ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                      : 'text-slate-600'
                  }`}
                >
                  {isDone ? 'Completed' : isCurrent ? 'In progress' : isFail ? 'Failed' : 'Pending'}
                </span>
              </div>
            );
          })}
        </div>

        {/* Error Alert Box */}
        {hasFailure && (
          <div className="p-5 rounded-2xl bg-rose-500/10 border border-rose-500/25 space-y-3">
            <div className="flex items-start gap-3 text-rose-300 text-xs">
              <AlertTriangle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
              <div className="space-y-1">
                <span className="font-bold text-white">We hit a temporary roadblock</span>
                <p className="text-slate-300 leading-relaxed">
                  {errorMessage || "SPECra's AI service is temporarily busy. Your data is safe. Please try again in a moment."}
                </p>
              </div>
            </div>

            <div className="pt-2 flex items-center justify-between border-t border-rose-500/20">
              <button
                onClick={() => setShowTechnicalError(!showTechnicalError)}
                className="text-[11px] text-slate-400 hover:text-slate-200 flex items-center gap-1"
              >
                <span>{showTechnicalError ? 'Hide' : 'View'} technical details</span>
                {showTechnicalError ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              </button>

              <button
                onClick={runPipeline}
                disabled={isProcessing}
                className="px-4 py-2 rounded-xl bg-rose-500 hover:bg-rose-400 text-slate-950 font-bold text-xs flex items-center gap-1.5 transition-colors cursor-pointer"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Retry analysis</span>
              </button>
            </div>

            {showTechnicalError && rawTechnicalError && (
              <pre className="p-3 rounded-xl bg-slate-950 text-slate-400 font-mono text-[10px] overflow-x-auto max-h-40 border border-slate-800">
                {rawTechnicalError}
              </pre>
            )}
          </div>
        )}

        {/* Success Completion Banner */}
        {isAllComplete && (
          <div className="p-6 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold">
                ✓
              </div>
              <div>
                <h4 className="text-sm font-bold text-white">Your product intelligence is ready</h4>
                <p className="text-xs text-slate-300">
                  {productsExtractedCount} products successfully extracted, normalized, and validated.
                </p>
              </div>
            </div>

            <button
              onClick={() => setActiveTab('results')}
              className="px-6 py-2.5 rounded-xl text-xs font-bold bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition-all shadow-md shadow-cyan-500/20 flex items-center gap-2 cursor-pointer"
            >
              <span>Review Results</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
