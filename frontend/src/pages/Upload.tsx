import React, { useState } from 'react';
import {
  UploadCloud,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import { uploadDataset } from '../api/ingestion';
import { formatErrorMessage } from '../api/client';
import { WorkflowProgress } from '../components/layout/WorkflowProgress';
import type { IngestionUploadResponse } from '../types/api';

export const Upload: React.FC = () => {
  const { setSelectedJobId, setActiveTab } = useApp();
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadResult, setUploadResult] = useState<IngestionUploadResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [showFields, setShowFields] = useState<boolean>(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setUploadResult(null);
      setErrorMessage(null);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
      setUploadResult(null);
      setErrorMessage(null);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setErrorMessage(null);

    try {
      const result = await uploadDataset(file);
      setUploadResult(result);
      setSelectedJobId(result.job_id);
    } catch (err: any) {
      setErrorMessage(formatErrorMessage(err));
    } finally {
      setUploading(false);
    }
  };

  const handleContinue = () => {
    setActiveTab('understand');
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-12">
      {/* Workflow Stepper */}
      <WorkflowProgress currentTab="upload" completedTabs={[]} />

      {/* Main Upload Card */}
      <div className="specra-panel rounded-3xl p-8 border border-slate-800 space-y-8">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">
            Start with your product catalog
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Upload the CSV or Excel file containing your product information. SPECra will automatically understand its structure.
          </p>
        </div>

        {/* Drag & Drop Area */}
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          className="border-2 border-dashed border-slate-700 hover:border-cyan-500/60 rounded-2xl p-10 text-center transition-all bg-slate-950/40 hover:bg-slate-900/40 cursor-pointer relative"
        >
          <input
            type="file"
            accept=".csv, .xlsx, .xls"
            onChange={handleFileChange}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          />

          <div className="flex flex-col items-center justify-center space-y-3 pointer-events-none">
            <div className="w-14 h-14 rounded-2xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center shadow-lg shadow-cyan-500/10">
              <UploadCloud className="w-7 h-7" />
            </div>

            <div className="space-y-1">
              <span className="text-sm font-semibold text-slate-200">
                {file ? file.name : 'Drag and drop your catalog here, or browse files'}
              </span>
              <p className="text-xs text-slate-400">
                Supports CSV, XLSX, and XLS files up to 50MB
              </p>
            </div>

            {file && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 text-xs font-semibold">
                <CheckCircle2 className="w-3.5 h-3.5" />
                {(file.size / 1024).toFixed(1)} KB selected
              </span>
            )}
          </div>
        </div>

        {/* Upload Action Button */}
        {file && !uploadResult && (
          <div className="flex justify-end">
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="px-6 py-3 rounded-xl text-xs font-bold bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition-all shadow-lg shadow-cyan-500/20 flex items-center gap-2 cursor-pointer disabled:opacity-50"
            >
              {uploading ? (
                <>
                  <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                  <span>Understanding catalog...</span>
                </>
              ) : (
                <>
                  <span>Upload & Analyze Structure</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        )}

        {/* Error Alert */}
        {errorMessage && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-3">
            <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Upload Success & Detected Fields Overview */}
        {uploadResult && (
          <div className="space-y-6 pt-4 border-t border-slate-800 animate-fadeIn">
            <div className="p-6 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold">
                    ✓
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white">Catalog Successfully Uploaded</h3>
                    <p className="text-xs text-slate-300">
                      SPECra detected {uploadResult.row_count || uploadResult.processed_records || 1} products and {uploadResult.schema_summary?.columns?.length || 6} columns.
                    </p>
                  </div>
                </div>

                <button
                  onClick={handleContinue}
                  className="px-6 py-2.5 rounded-xl text-xs font-bold bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition-all shadow-md shadow-cyan-500/20 flex items-center gap-1.5"
                >
                  <span>Continue</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* High-Level Metric Pills */}
              <div className="grid grid-cols-3 gap-3 pt-2 text-center">
                <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                  <div className="text-[10px] text-slate-400 uppercase font-semibold">Products Detected</div>
                  <div className="text-lg font-bold text-white mt-0.5">{uploadResult.row_count || uploadResult.processed_records || 1}</div>
                </div>
                <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                  <div className="text-[10px] text-slate-400 uppercase font-semibold">Fields Detected</div>
                  <div className="text-lg font-bold text-cyan-400 mt-0.5">{uploadResult.schema_summary?.columns?.length || 6}</div>
                </div>
                <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                  <div className="text-[10px] text-slate-400 uppercase font-semibold">Quality Status</div>
                  <div className="text-lg font-bold text-emerald-400 mt-0.5">Ready</div>
                </div>
              </div>
            </div>

            {/* Expandable Detected Fields View */}
            <div className="border border-slate-800 rounded-2xl p-4 bg-slate-950/40 space-y-3">
              <button
                onClick={() => setShowFields(!showFields)}
                className="w-full flex items-center justify-between text-xs font-semibold text-slate-300 hover:text-white"
              >
                <span>View detected fields ({uploadResult.schema_summary?.columns?.length || 0})</span>
                {showFields ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>

              {showFields && (
                <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-800/80">
                  {(uploadResult.schema_summary?.columns || []).map((col: string) => (
                    <span
                      key={col}
                      className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-xs font-mono text-slate-300"
                    >
                      {col}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
