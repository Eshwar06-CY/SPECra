import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  Table as TableIcon,
  Layers,
  SlidersHorizontal,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import { listAllJobs } from '../api/ingestion';
import { getExportPreview, downloadExportFile } from '../api/export';
import { formatErrorMessage } from '../api/client';
import { WorkflowProgress } from '../components/layout/WorkflowProgress';
import type { ExportPreviewResponse } from '../types/api';

export const Export: React.FC = () => {
  const { selectedJobId, setSelectedJobId } = useApp();
  const [previewData, setPreviewData] = useState<ExportPreviewResponse | null>(null);
  const [downloading, setDownloading] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const data = await listAllJobs();
        if (!selectedJobId && data.length > 0) {
          setSelectedJobId(data[0].id);
        }
      } catch (err) {
        console.error(err);
      }
    };
    fetchJobs();
  }, []);

  const fetchPreview = async (jobId: string) => {
    setErrorMessage(null);
    try {
      const data = await getExportPreview(jobId, 5);
      setPreviewData(data);
    } catch (err: any) {
      setPreviewData(null);
      setErrorMessage(formatErrorMessage(err));
    }
  };

  useEffect(() => {
    if (selectedJobId) {
      fetchPreview(selectedJobId);
    }
  }, [selectedJobId]);

  const handleDownload = async (format: 'csv' | 'xlsx', type: string) => {
    if (!selectedJobId) return;
    setDownloading(`${type}-${format}`);
    try {
      await downloadExportFile(selectedJobId, format);
    } catch (err: any) {
      setErrorMessage(formatErrorMessage(err));
    } finally {
      setDownloading(null);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      {/* Workflow Stepper */}
      <WorkflowProgress
        currentTab="export"
        completedTabs={['upload', 'understand', 'requirements', 'process', 'results']}
      />

      {/* Main Download Card */}
      <div className="specra-panel rounded-3xl p-8 border border-slate-800 space-y-8">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">
            Your data is ready to use
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Download your structured product intelligence in the format you need.
          </p>
        </div>

        {/* 3 Download Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Card 1: Custom Results */}
          <div className="specra-card rounded-2xl p-6 border border-slate-800 flex flex-col justify-between space-y-4 hover:border-slate-700 transition-colors">
            <div className="space-y-2">
              <div className="w-10 h-10 rounded-xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center">
                <SlidersHorizontal className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-white">Custom Results</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Only the exact fields and attributes you requested during configuration.
              </p>
            </div>

            <div className="flex items-center gap-2 pt-2">
              <button
                onClick={() => handleDownload('csv', 'custom')}
                disabled={downloading !== null || !selectedJobId}
                className="flex-1 py-2.5 rounded-xl text-xs font-semibold bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700/80 transition-all text-center disabled:opacity-50 cursor-pointer"
              >
                {downloading === 'custom-csv' ? 'Preparing...' : 'Download CSV'}
              </button>
              <button
                onClick={() => handleDownload('xlsx', 'custom')}
                disabled={downloading !== null || !selectedJobId}
                className="flex-1 py-2.5 rounded-xl text-xs font-bold bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition-all text-center shadow-md shadow-cyan-500/20 disabled:opacity-50 cursor-pointer"
              >
                {downloading === 'custom-xlsx' ? 'Preparing...' : 'Download Excel'}
              </button>
            </div>
          </div>

          {/* Card 2: Full Product Data */}
          <div className="specra-card rounded-2xl p-6 border border-cyan-500/40 bg-cyan-950/10 flex flex-col justify-between space-y-4 shadow-lg shadow-cyan-500/10 ring-1 ring-cyan-500/20">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="w-10 h-10 rounded-xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center">
                  <Sparkles className="w-5 h-5" />
                </div>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 uppercase tracking-wider">
                  Popular
                </span>
              </div>
              <h3 className="text-base font-bold text-white">Full Product Data</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Complete standardized product dataset with normalized units, packaging, and brand taxonomy.
              </p>
            </div>

            <div className="flex items-center gap-2 pt-2">
              <button
                onClick={() => handleDownload('csv', 'full')}
                disabled={downloading !== null || !selectedJobId}
                className="flex-1 py-2.5 rounded-xl text-xs font-semibold bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700/80 transition-all text-center disabled:opacity-50 cursor-pointer"
              >
                {downloading === 'full-csv' ? 'Preparing...' : 'Download CSV'}
              </button>
              <button
                onClick={() => handleDownload('xlsx', 'full')}
                disabled={downloading !== null || !selectedJobId}
                className="flex-1 py-2.5 rounded-xl text-xs font-bold bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition-all text-center shadow-md shadow-cyan-500/20 disabled:opacity-50 cursor-pointer"
              >
                {downloading === 'full-xlsx' ? 'Preparing...' : 'Download Excel'}
              </button>
            </div>
          </div>

          {/* Card 3: UniHack Delivery Format */}
          <div className="specra-card rounded-2xl p-6 border border-slate-800 flex flex-col justify-between space-y-4 hover:border-slate-700 transition-colors">
            <div className="space-y-2">
              <div className="w-10 h-10 rounded-xl bg-purple-500/10 text-purple-400 flex items-center justify-center">
                <Layers className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-white">UniHack Delivery Format</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                252-column standardized delivery format adhering to strict enterprise catalog schemas.
              </p>
            </div>

            <div className="flex items-center gap-2 pt-2">
              <button
                onClick={() => handleDownload('csv', 'unihack')}
                disabled={downloading !== null || !selectedJobId}
                className="flex-1 py-2.5 rounded-xl text-xs font-semibold bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700/80 transition-all text-center disabled:opacity-50 cursor-pointer"
              >
                {downloading === 'unihack-csv' ? 'Preparing...' : 'Download CSV'}
              </button>
              <button
                onClick={() => handleDownload('xlsx', 'unihack')}
                disabled={downloading !== null || !selectedJobId}
                className="flex-1 py-2.5 rounded-xl text-xs font-bold bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition-all text-center shadow-md shadow-cyan-500/20 disabled:opacity-50 cursor-pointer"
              >
                {downloading === 'unihack-xlsx' ? 'Preparing...' : 'Download Excel'}
              </button>
            </div>
          </div>
        </div>

        {errorMessage && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
            {errorMessage}
          </div>
        )}

        {/* Live Export Preview */}
        {previewData && (
          <div className="space-y-3 pt-4 border-t border-slate-800">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-bold text-white">
                <TableIcon className="w-4 h-4 text-cyan-400" />
                <span>Dataset Preview</span>
              </div>
              <span className="text-[11px] text-slate-400 font-medium">
                Showing sample rows from {previewData.headers.length} standardized columns
              </span>
            </div>

            <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-950/40">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-900 text-slate-300 font-semibold border-b border-slate-800 sticky top-0">
                  <tr>
                    {previewData.headers.slice(0, 8).map((h) => (
                      <th key={h} className="p-3 whitespace-nowrap border-r border-slate-800/60 font-mono text-[11px]">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {previewData.sample_rows.map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-900/40 font-mono text-[11px]">
                      {previewData.headers.slice(0, 8).map((h) => (
                        <td key={h} className="p-3 truncate max-w-[200px] border-r border-slate-800/40 text-slate-200">
                          {row[h] !== null && row[h] !== undefined && row[h] !== '' ? String(row[h]) : '—'}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
