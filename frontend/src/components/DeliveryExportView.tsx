import React, { useState, useEffect } from 'react';
import {
  FileSpreadsheet,
  AlertTriangle,
  FileText,
  Table,
} from 'lucide-react';
import type { ProcessingJob, ExportPreview } from '../types';
import { getExportPreview, downloadExport } from '../services/api';

interface DeliveryExportViewProps {
  jobs: ProcessingJob[];
}

export const DeliveryExportView: React.FC<DeliveryExportViewProps> = ({ jobs }) => {
  const [selectedJobId, setSelectedJobId] = useState<string>(jobs[0]?.id || '');
  const [previewData, setPreviewData] = useState<ExportPreview | null>(null);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState<'csv' | 'xlsx' | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (jobs.length > 0 && !selectedJobId) {
      setSelectedJobId(jobs[0].id);
    }
  }, [jobs]);

  useEffect(() => {
    if (selectedJobId) {
      fetchPreview(selectedJobId);
    }
  }, [selectedJobId]);

  const fetchPreview = async (jobId: string) => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await getExportPreview(jobId, 5);
      setPreviewData(data);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to load export preview.');
      setPreviewData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (format: 'csv' | 'xlsx') => {
    if (!selectedJobId) return;
    setDownloading(format);
    try {
      await downloadExport(selectedJobId, format);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to download delivery dataset.');
    } finally {
      setDownloading(null);
    }
  };

  return (
    <div className="space-y-8">
      {/* Top Banner & Downloader Card */}
      <div className="glass-panel rounded-2xl p-8 border border-slate-800 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
        <div className="space-y-2 max-w-2xl">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-1 rounded-md text-xs font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              Exact 252 Static Headers
            </span>
            <span className="px-2.5 py-1 rounded-md text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              UniHack Format Guaranteed
            </span>
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">
            UniHack Delivery Output Export
          </h2>
          <p className="text-xs text-slate-400 leading-relaxed">
            Exports verified canonical intelligence, enriched dimensions, and raw metadata mapped
            directly into the exact 252 delivery headers in strict schema order.
          </p>

          {/* Job Selector */}
          <div className="pt-2 flex items-center gap-3">
            <label className="text-xs text-slate-400">Target Dataset:</label>
            <select
              value={selectedJobId}
              onChange={(e) => setSelectedJobId(e.target.value)}
              className="glass-input text-xs px-3 py-1.5 rounded-lg text-slate-200"
            >
              {jobs.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.filename} ({j.total_records} records)
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Download Buttons */}
        <div className="flex flex-col sm:flex-row items-center gap-3 w-full lg:w-auto">
          <button
            onClick={() => handleDownload('csv')}
            disabled={downloading !== null || !selectedJobId}
            className="w-full sm:w-auto px-5 py-2.5 rounded-xl text-sm font-semibold bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition-all shadow-md shadow-cyan-500/20 flex items-center justify-center gap-2 disabled:opacity-50"
          >
            <FileText className="w-4 h-4" />
            {downloading === 'csv' ? 'Generating CSV...' : 'Download Delivery CSV'}
          </button>
          <button
            onClick={() => handleDownload('xlsx')}
            disabled={downloading !== null || !selectedJobId}
            className="w-full sm:w-auto px-5 py-2.5 rounded-xl text-sm font-semibold bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
          >
            <FileSpreadsheet className="w-4 h-4" />
            {downloading === 'xlsx' ? 'Generating XLSX...' : 'Download Delivery Excel'}
          </button>
        </div>
      </div>

      {loading && (
        <div className="text-center py-8 text-cyan-400 text-sm font-semibold flex items-center justify-center gap-2">
          <div className="w-4 h-4 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
          Loading 252-column dataset preview...
        </div>
      )}

      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {previewData && (
        <div className="space-y-6">
          {/* Fill Rate & Metric Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="glass-card rounded-xl p-4 border border-slate-800">
              <div className="text-xs text-slate-400 font-medium">Dataset Records</div>
              <div className="text-2xl font-bold text-white mt-1">
                {previewData.summary.total_products}
              </div>
            </div>
            <div className="glass-card rounded-xl p-4 border border-slate-800">
              <div className="text-xs text-slate-400 font-medium">Static Delivery Headers</div>
              <div className="text-2xl font-bold text-cyan-400 mt-1">
                {previewData.summary.total_headers}
              </div>
            </div>
            <div className="glass-card rounded-xl p-4 border border-slate-800">
              <div className="text-xs text-slate-400 font-medium">Populated Fields</div>
              <div className="text-2xl font-bold text-emerald-400 mt-1">
                {previewData.summary.fields_populated_count}
              </div>
            </div>
            <div className="glass-card rounded-xl p-4 border border-slate-800">
              <div className="text-xs text-slate-400 font-medium">Fill Rate</div>
              <div className="text-2xl font-bold text-indigo-400 mt-1">
                {previewData.summary.fill_rate_percent}%
              </div>
            </div>
          </div>

          {/* Sample Rows Table Preview */}
          <div className="glass-panel rounded-2xl p-6 border border-slate-800">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Table className="w-4 h-4 text-cyan-400" />
                Live 252-Column Data Grid Preview (First 5 Rows)
              </h3>
              <span className="text-xs text-slate-400 font-mono">
                Showing {previewData.sample_rows.length} rows &times; 252 columns
              </span>
            </div>

            <div className="overflow-x-auto max-h-96 rounded-xl border border-slate-800">
              <table className="w-full text-left text-xs text-slate-300 whitespace-nowrap">
                <thead className="sticky top-0 bg-slate-900 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800 z-10">
                  <tr>
                    <th className="py-2.5 px-3 bg-slate-950 border-r border-slate-800">#</th>
                    {previewData.headers.map((h, i) => (
                      <th key={i} className="py-2.5 px-3 border-r border-slate-800/60 font-semibold">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/40 font-mono">
                  {previewData.sample_rows.map((row, rIdx) => (
                    <tr key={rIdx} className="hover:bg-slate-900/40 transition-colors">
                      <td className="py-2.5 px-3 bg-slate-950/80 font-bold text-slate-500 border-r border-slate-800">
                        {rIdx + 1}
                      </td>
                      {previewData.headers.map((h, cIdx) => (
                        <td
                          key={cIdx}
                          className={`py-2 px-3 border-r border-slate-800/30 ${
                            row[h] ? 'text-slate-200' : 'text-slate-600 italic'
                          }`}
                        >
                          {row[h] || '—'}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
