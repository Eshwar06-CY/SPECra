import React, { useState } from 'react';
import {
  UploadCloud,
  FileSpreadsheet,
  CheckCircle2,
  AlertCircle,
  Sparkles,
} from 'lucide-react';
import type { ProcessingJob } from '../types';
import { uploadDataset, analyzeJob } from '../services/api';

interface DatasetIngestionProps {
  jobs: ProcessingJob[];
  fetchJobs: () => void;
  onSelectProduct?: (productId: string) => void;
}

export const DatasetIngestion: React.FC<DatasetIngestionProps> = ({
  jobs,
  fetchJobs,
}) => {
  const [uploading, setUploading] = useState(false);
  const [analyzingJobId, setAnalyzingJobId] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [processLimit, setProcessLimit] = useState<number>(1);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const res = await uploadDataset(file);
      setSuccessMsg(`Successfully ingested ${res.total_records} records from "${file.name}"!`);
      fetchJobs();
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to upload dataset.');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleRunAnalysis = async (jobId: string) => {
    setAnalyzingJobId(jobId);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const res = await analyzeJob(jobId, processLimit);
      setSuccessMsg(
        `AI Intelligence run complete: ${res.processed} processed, ${res.failed} failed.`
      );
      fetchJobs();
    } catch (err: any) {
      setErrorMsg(
        err.response?.data?.detail || 'Error occurred during AI intelligence execution.'
      );
    } finally {
      setAnalyzingJobId(null);
    }
  };

  return (
    <div className="space-y-8">
      {/* Top Banner / Upload Card */}
      <div className="glass-panel rounded-2xl p-8 border border-slate-800 relative overflow-hidden">
        <div className="absolute -right-12 -bottom-12 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="max-w-2xl">
          <h2 className="text-2xl font-bold text-white tracking-tight">
            Ingest Industrial Product Catalog Datasets
          </h2>
          <p className="text-slate-400 text-sm mt-2 leading-relaxed">
            Upload unstandardized CSV or Excel datasets (e.g. UniHack 1000-row catalog).
            The ingestion engine parses headers, preserves raw records, and tracks batch job status.
          </p>

          {/* Upload Dropzone */}
          <div className="mt-6">
            <label className="flex flex-col items-center justify-center border-2 border-dashed border-slate-700/80 hover:border-cyan-500/50 hover:bg-slate-900/50 transition-all rounded-xl p-8 cursor-pointer group">
              <UploadCloud className="w-12 h-12 text-slate-500 group-hover:text-cyan-400 transition-colors" />
              <span className="text-sm font-semibold text-slate-300 group-hover:text-white mt-3">
                {uploading ? 'Ingesting Dataset...' : 'Click to browse or drag & drop catalog file'}
              </span>
              <span className="text-xs text-slate-500 mt-1">Supports CSV, XLSX, and XLS</span>
              <input
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={handleFileUpload}
                disabled={uploading}
                className="hidden"
              />
            </label>
          </div>

          {/* Notifications */}
          {errorMsg && (
            <div className="mt-4 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm flex items-center gap-3">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}
          {successMsg && (
            <div className="mt-4 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-sm flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}
        </div>
      </div>

      {/* Ingestion Batch Jobs Table */}
      <div className="glass-panel rounded-2xl p-6 border border-slate-800">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg font-bold text-white">Ingestion Jobs</h3>
            <p className="text-xs text-slate-400 mt-1">
              Active and completed catalog batches available for AI Product Intelligence.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <label className="text-xs text-slate-400 flex items-center gap-2">
              <span>Batch Limit:</span>
              <select
                value={processLimit}
                onChange={(e) => setProcessLimit(Number(e.target.value))}
                className="glass-input text-xs px-2.5 py-1.5 rounded-lg text-slate-200"
              >
                <option value={1}>1 Product (Dev / Test)</option>
                <option value={10}>10 Products</option>
                <option value={50}>50 Products</option>
                <option value={100}>100 Products</option>
                <option value={1000}>1000 Products (Full Run)</option>
              </select>
            </label>
          </div>
        </div>

        {jobs.length === 0 ? (
          <div className="text-center py-12 text-slate-500 text-sm">
            No datasets uploaded yet. Upload a CSV catalog above to begin.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-900/60 text-slate-400 uppercase text-xs tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-3.5 px-4">Dataset Name</th>
                  <th className="py-3.5 px-4">File Type</th>
                  <th className="py-3.5 px-4">Records</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4">Ingested At</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {jobs.map((job) => (
                  <tr key={job.id} className="hover:bg-slate-900/40 transition-colors">
                    <td className="py-4 px-4 font-medium text-white flex items-center gap-3">
                      <FileSpreadsheet className="w-5 h-5 text-cyan-400" />
                      <div>
                        <div className="font-semibold">{job.filename}</div>
                        <div className="text-xs text-slate-500 font-mono">{job.id}</div>
                      </div>
                    </td>
                    <td className="py-4 px-4 uppercase text-xs font-semibold text-slate-400">
                      {job.file_type}
                    </td>
                    <td className="py-4 px-4">
                      <span className="font-semibold text-white">{job.total_records}</span> rows
                    </td>
                    <td className="py-4 px-4">
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        {job.status}
                      </span>
                    </td>
                    <td className="py-4 px-4 text-xs text-slate-400">
                      {new Date(job.created_at).toLocaleString()}
                    </td>
                    <td className="py-4 px-4 text-right">
                      <button
                        onClick={() => handleRunAnalysis(job.id)}
                        disabled={analyzingJobId === job.id}
                        className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/40 transition-all disabled:opacity-50"
                      >
                        <Sparkles className="w-3.5 h-3.5" />
                        {analyzingJobId === job.id
                          ? 'Extracting AI Intelligence...'
                          : `Run AI Extraction (${processLimit})`}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
