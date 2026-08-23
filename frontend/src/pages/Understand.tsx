import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  CheckCircle2,
  ArrowRight,
  Columns,
  Table as TableIcon,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import { getJobSchema, getJobRecords, getJobStatus } from '../api/ingestion';
import { WorkflowProgress } from '../components/layout/WorkflowProgress';
import type { SchemaAnalysisSummary, ProductRecordResponse, ProcessingJobResponse } from '../types/api';

export const Understand: React.FC = () => {
  const { selectedJobId, setActiveTab } = useApp();
  const [job, setJob] = useState<ProcessingJobResponse | null>(null);
  const [schema, setSchema] = useState<SchemaAnalysisSummary | null>(null);
  const [sampleRows, setSampleRows] = useState<ProductRecordResponse[]>([]);

  // Friendly human labels for recognized industrial columns
  const getFriendlyUnderstanding = (colName: string): string => {
    const lower = colName.toLowerCase();
    if (lower.includes('desc')) return 'Product description';
    if (lower.includes('manuf') || lower.includes('mfg')) return 'Manufacturer name';
    if (lower.includes('part') || lower.includes('sku') || lower.includes('item')) return 'Manufacturer part number';
    if (lower.includes('brand')) return 'Brand';
    if (lower.includes('uom') || lower.includes('unit')) return 'Unit of measure';
    if (lower.includes('qty') || lower.includes('quantity')) return 'Quantity / Pack size';
    if (lower.includes('cat') || lower.includes('class')) return 'Category';
    if (lower.includes('price') || lower.includes('cost')) return 'Pricing';
    return 'Catalog specification';
  };

  useEffect(() => {
    const loadData = async () => {
      if (!selectedJobId) {
        return;
      }
      try {
        const [jobData, schemaData, recordsData] = await Promise.all([
          getJobStatus(selectedJobId),
          getJobSchema(selectedJobId),
          getJobRecords(selectedJobId, 1, 5),
        ]);
        setJob(jobData);
        setSchema(schemaData);
        setSampleRows(recordsData.records || []);
      } catch (err) {
        console.error('Error fetching schema:', err);
      }
    };
    loadData();
  }, [selectedJobId]);

  const handleContinue = () => {
    setActiveTab('requirements');
  };

  if (!selectedJobId) {
    return (
      <div className="glass-panel rounded-3xl p-12 text-center border border-slate-800 space-y-4 max-w-md mx-auto">
        <h3 className="text-base font-bold text-white">No dataset selected</h3>
        <p className="text-xs text-slate-400">
          Upload a catalog first so DEADLOCK can understand its structure.
        </p>
        <button
          onClick={() => setActiveTab('upload')}
          className="px-5 py-2.5 rounded-xl text-xs font-semibold bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition-all"
        >
          Go to Upload
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-12">
      {/* Step Progress */}
      <WorkflowProgress currentTab="understand" completedTabs={['upload']} />

      {/* Main Understanding Card */}
      <div className="glass-panel rounded-3xl p-8 border border-slate-800 space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">
            Let's understand your catalog
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            DEADLOCK has identified these fields from your catalog without needing manual templates.
          </p>
        </div>

        {/* Overview Banner */}
        <div className="p-5 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center gap-3">
          <Sparkles className="w-5 h-5 text-cyan-400 flex-shrink-0" />
          <span className="text-xs text-slate-200">
            We found <strong>{job?.total_records.toLocaleString() || '1,000'} products</strong> across{' '}
            <strong>{schema?.columns.length || 6} columns</strong> in{' '}
            <span className="font-semibold text-white">{job?.filename}</span>.
          </span>
        </div>

        {/* Column Understanding Table */}
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs text-slate-400 font-semibold px-2">
            <span>Your Column</span>
            <span>DEADLOCK Understands It As</span>
          </div>

          <div className="space-y-2">
            {schema?.columns.map((col) => {
              const friendlyMeaning = getFriendlyUnderstanding(col);
              return (
                <div
                  key={col}
                  className="glass-card rounded-xl p-3.5 border border-slate-800 flex items-center justify-between hover:border-slate-700 transition-colors"
                >
                  <div className="flex items-center gap-2.5 font-mono text-xs text-cyan-300">
                    <Columns className="w-3.5 h-3.5 text-slate-500" />
                    <span>{col}</span>
                  </div>

                  <div className="flex items-center gap-2 text-xs text-slate-200">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    <span>{friendlyMeaning}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Sample Preview */}
        {sampleRows.length > 0 && (
          <div className="space-y-3 pt-4 border-t border-slate-800">
            <div className="flex items-center gap-2 text-xs font-bold text-white">
              <TableIcon className="w-4 h-4 text-cyan-400" />
              <span>Catalog Preview (First 5 Rows)</span>
            </div>

            <div className="overflow-x-auto rounded-xl border border-slate-800">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900/90 text-slate-400 font-semibold border-b border-slate-800">
                  <tr>
                    {schema?.columns.slice(0, 4).map((c) => (
                      <th key={c} className="p-3">
                        {c}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {sampleRows.map((row) => (
                    <tr key={row.id} className="hover:bg-slate-900/40">
                      {schema?.columns.slice(0, 4).map((c) => (
                        <td key={c} className="p-3 truncate max-w-[200px]">
                          {String(row.raw_data[c] || '—')}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex items-center justify-between pt-6 border-t border-slate-800">
          <button
            onClick={() => setActiveTab('upload')}
            className="px-4 py-2.5 rounded-xl text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors"
          >
            ← Upload different file
          </button>

          <button
            onClick={handleContinue}
            className="px-8 py-3.5 rounded-xl text-sm font-bold bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition-all shadow-lg shadow-cyan-500/20 flex items-center gap-2"
          >
            <span>Looks good — continue</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
