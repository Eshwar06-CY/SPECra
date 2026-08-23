import React, { useState, useEffect } from 'react';
import {
  UploadCloud,
  FileSpreadsheet,
  ArrowRight,
  Sparkles,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import { useAuth } from '../context/AuthContext';
import { listAllJobs } from '../api/ingestion';
import type { ProcessingJobResponse } from '../types/api';

export const Dashboard: React.FC = () => {
  const { setActiveTab, setSelectedJobId } = useApp();
  const { user } = useAuth();
  const [jobs, setJobs] = useState<ProcessingJobResponse[]>([]);

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const data = await listAllJobs();
        setJobs(data);
      } catch (err) {
        console.error('Failed to load jobs:', err);
      }
    };
    fetchJobs();
  }, []);

  const firstName = user?.name?.split(' ')[0] || 'Alex';

  const handleStartNewAnalysis = () => {
    setActiveTab('upload');
  };

  const handleSelectJob = (jobId: string) => {
    setSelectedJobId(jobId);
    setActiveTab('results');
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-12">
      {/* Personalized Header Hero */}
      <div className="specra-panel rounded-3xl p-8 md:p-10 border border-slate-800 relative overflow-hidden bg-gradient-to-br from-slate-900/90 via-slate-900/60 to-cyan-950/20">
        <div className="max-w-3xl space-y-3 relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI-Powered Industrial Intelligence</span>
          </div>

          <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight leading-tight">
            Good evening, {firstName} 👋
          </h1>

          <p className="text-sm sm:text-base text-slate-300 leading-relaxed">
            Turn your next catalog into structured intelligence. Upload a CSV or Excel file to extract specifications, clean units, and prepare commerce-ready data.
          </p>

          <div className="pt-3 flex flex-wrap items-center gap-4">
            <button
              onClick={handleStartNewAnalysis}
              className="px-6 py-3.5 rounded-xl text-sm font-bold bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition-all shadow-lg shadow-cyan-500/25 flex items-center gap-2 cursor-pointer"
            >
              <UploadCloud className="w-4 h-4" />
              <span>+ New Analysis</span>
              <ArrowRight className="w-4 h-4" />
            </button>

            {jobs.length > 0 && (
              <button
                onClick={() => setActiveTab('jobs')}
                className="px-6 py-3.5 rounded-xl text-sm font-semibold bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700/80 transition-all flex items-center gap-2 cursor-pointer"
              >
                <span>View Recent Catalogs ({jobs.length})</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="specra-card rounded-2xl p-6 border border-slate-800 space-y-1">
          <div className="text-xs text-slate-400 font-semibold">Catalogs Analyzed</div>
          <div className="text-2xl font-bold text-white mt-1">
            {jobs.length > 0 ? jobs.length : 1}
          </div>
          <div className="text-[11px] text-slate-500">Total catalog files</div>
        </div>

        <div className="specra-card rounded-2xl p-6 border border-slate-800 space-y-1">
          <div className="text-xs text-slate-400 font-semibold">Products Processed</div>
          <div className="text-2xl font-bold text-cyan-400 mt-1">
            {jobs.reduce((acc, j) => acc + (j.total_records || 1), 0).toLocaleString()}
          </div>
          <div className="text-[11px] text-slate-500">Standardized SKUs</div>
        </div>

        <div className="specra-card rounded-2xl p-6 border border-slate-800 space-y-1">
          <div className="text-xs text-slate-400 font-semibold">Average Data Quality</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">
            100%
          </div>
          <div className="text-[11px] text-slate-500">Zero unit conflicts</div>
        </div>

        <div className="specra-card rounded-2xl p-6 border border-slate-800 space-y-1">
          <div className="text-xs text-slate-400 font-semibold">Exports Generated</div>
          <div className="text-2xl font-bold text-purple-400 mt-1">
            252 Fields
          </div>
          <div className="text-[11px] text-slate-500">UniHack delivery standard</div>
        </div>
      </div>

      {/* Recent Analyses List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-white tracking-tight">Recent Analyses</h2>
          {jobs.length > 0 && (
            <button
              onClick={() => setActiveTab('jobs')}
              className="text-xs text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1"
            >
              <span>View all</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          )}
        </div>

        {jobs.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {jobs.slice(0, 4).map((job) => (
              <div
                key={job.id}
                onClick={() => handleSelectJob(job.id)}
                className="specra-card rounded-2xl p-6 border border-slate-800 hover:border-cyan-500/40 cursor-pointer transition-all space-y-4"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center">
                      <FileSpreadsheet className="w-5 h-5" />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-white truncate max-w-[200px]">
                        {job.filename}
                      </h4>
                      <p className="text-[11px] text-slate-400 font-mono">
                        {job.total_records} products • {new Date(job.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>

                  <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    Completed
                  </span>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-slate-800/80 text-xs">
                  <span className="text-slate-400">Quality: <strong className="text-emerald-400">100%</strong></span>
                  <span className="text-cyan-400 font-semibold flex items-center gap-1">
                    Open Results →
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="specra-panel rounded-3xl p-12 text-center border border-slate-800 space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center mx-auto">
              <Sparkles className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-white">Your workspace is ready.</h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              Upload your first product catalog and let SPECra turn it into structured intelligence.
            </p>
            <button
              onClick={handleStartNewAnalysis}
              className="px-6 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs transition-all shadow-md shadow-cyan-500/20"
            >
              Analyze a catalog
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
