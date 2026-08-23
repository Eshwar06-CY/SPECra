import React, { useState } from 'react';
import {
  Sparkles,
  ArrowRight,
  CheckCircle2,
  Edit3,
  Check,
  SlidersHorizontal,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import { previewProductQuery, type QueryPreviewResponse } from '../api/query';
import { formatErrorMessage } from '../api/client';
import { WorkflowProgress } from '../components/layout/WorkflowProgress';

export type CatalogMode = 'standard' | 'focused' | 'custom';

export const Requirements: React.FC = () => {
  const { selectedJobId, setActiveTab, setActiveQuery } = useApp();
  const [selectedMode, setSelectedMode] = useState<CatalogMode>('standard');
  const [customPrompt, setCustomPrompt] = useState<string>(
    'Find the brand, manufacturer, product type, dimensions and packaging quantity for all sanding products.'
  );
  const [selectedChips, setSelectedChips] = useState<string[]>([
    'Brand',
    'Manufacturer',
    'Product type',
    'Dimensions',
    'Packaging',
  ]);
  const [previewData, setPreviewData] = useState<QueryPreviewResponse | null>(null);
  const [previewing, setPreviewing] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const requirementChips = [
    'Brand',
    'Manufacturer',
    'Product type',
    'Dimensions',
    'Weight',
    'Packaging',
    'Part number',
    'Specifications',
    'Compliance',
    'Product descriptions',
  ];

  const handleToggleChip = (chip: string) => {
    if (selectedChips.includes(chip)) {
      setSelectedChips(selectedChips.filter((c) => c !== chip));
    } else {
      setSelectedChips([...selectedChips, chip]);
    }
  };

  const handlePreviewPlan = async () => {
    if (!selectedJobId || !customPrompt.trim()) return;
    setPreviewing(true);
    setErrorMessage(null);
    try {
      const res = await previewProductQuery(selectedJobId, customPrompt.trim());
      setPreviewData(res);
    } catch (err: any) {
      setErrorMessage(formatErrorMessage(err));
    } finally {
      setPreviewing(false);
    }
  };

  const handleStartAnalysis = () => {
    if (selectedMode !== 'standard' && customPrompt.trim()) {
      setActiveQuery(customPrompt.trim());
    } else {
      setActiveQuery(null);
    }
    setActiveTab('process');
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      {/* Workflow Stepper */}
      <WorkflowProgress currentTab="requirements" completedTabs={['upload', 'understand']} />

      {/* Main Container Card */}
      <div className="specra-panel rounded-3xl p-8 border border-slate-800 space-y-8">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">
            What would you like SPECra to find?
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Describe the information you need in natural language or select from domain specifications.
          </p>
        </div>

        {/* Natural Language Prompt Box */}
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <label className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-cyan-400" />
              <span>Describe what SPECra should extract</span>
            </label>
            <span className="text-[11px] text-slate-400 font-mono">SPECra Natural Intelligence</span>
          </div>

          <div className="relative">
            <textarea
              rows={3}
              value={customPrompt}
              onChange={(e) => {
                setCustomPrompt(e.target.value);
                setPreviewData(null);
              }}
              placeholder="Example: Find the brand, manufacturer, product type, dimensions and packaging quantity for all sanding products."
              className="specra-input w-full px-4 py-3 rounded-xl text-xs text-white placeholder:text-slate-500 resize-none"
            />
          </div>

          {/* Suggested Requirement Chips */}
          <div className="space-y-2 pt-1">
            <span className="text-[11px] text-slate-400 font-semibold uppercase tracking-wider">
              Suggested specifications & requirements:
            </span>
            <div className="flex flex-wrap gap-2">
              {requirementChips.map((chip) => {
                const isSelected = selectedChips.includes(chip);
                return (
                  <button
                    key={chip}
                    onClick={() => handleToggleChip(chip)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all border flex items-center gap-1.5 cursor-pointer ${
                      isSelected
                        ? 'bg-cyan-500/15 text-cyan-300 border-cyan-500/40 shadow-sm shadow-cyan-500/10'
                        : 'bg-slate-950/60 text-slate-400 border-slate-800 hover:border-slate-700 hover:text-white'
                    }`}
                  >
                    {isSelected && <Check className="w-3.5 h-3.5 text-cyan-400" />}
                    <span>{chip}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Mode Selection */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
            <div
              onClick={() => setSelectedMode('standard')}
              className={`p-4 rounded-xl border cursor-pointer transition-all space-y-1 ${
                selectedMode === 'standard'
                  ? 'bg-cyan-950/20 border-cyan-500 text-white'
                  : 'bg-slate-950/40 border-slate-800 text-slate-400 hover:border-slate-700'
              }`}
            >
              <div className="text-xs font-bold flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-cyan-400" />
                <span>Analyze the entire catalog</span>
              </div>
              <p className="text-[11px] text-slate-400">
                Process and standardize every item in the uploaded file.
              </p>
            </div>

            <div
              onClick={() => setSelectedMode('focused')}
              className={`p-4 rounded-xl border cursor-pointer transition-all space-y-1 ${
                selectedMode === 'focused'
                  ? 'bg-cyan-950/20 border-cyan-500 text-white'
                  : 'bg-slate-950/40 border-slate-800 text-slate-400 hover:border-slate-700'
              }`}
            >
              <div className="text-xs font-bold flex items-center gap-2">
                <SlidersHorizontal className="w-4 h-4 text-indigo-400" />
                <span>Focus on specific products</span>
              </div>
              <p className="text-[11px] text-slate-400">
                Target queries filtered by brand or product category.
              </p>
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <button
              onClick={handlePreviewPlan}
              disabled={previewing || !customPrompt.trim()}
              className="px-5 py-2.5 rounded-xl text-xs font-bold bg-indigo-500 hover:bg-indigo-400 text-slate-950 transition-all disabled:opacity-50 flex items-center gap-2 shadow-md shadow-indigo-500/20 cursor-pointer"
            >
              {previewing ? (
                <div className="w-3.5 h-3.5 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
              ) : (
                <Sparkles className="w-3.5 h-3.5" />
              )}
              <span>Interpret Request with SPECra</span>
            </button>
          </div>
        </div>

        {/* Structured Interpretation Box */}
        {previewData && (
          <div className="p-6 rounded-2xl bg-cyan-950/20 border border-cyan-500/40 space-y-4 animate-fadeIn">
            <div className="flex items-center justify-between border-b border-cyan-500/20 pb-3">
              <h4 className="text-xs font-bold text-cyan-300 uppercase tracking-wider flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-cyan-400" />
                <span>You've asked SPECra to find:</span>
              </h4>
              <button
                onClick={() => setPreviewData(null)}
                className="text-xs text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1"
              >
                <Edit3 className="w-3 h-3" />
                <span>Edit request</span>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="space-y-2 p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
                <span className="text-[11px] font-bold text-slate-400 uppercase">Product Scope:</span>
                {previewData.query_plan.filters.length > 0 ? (
                  <div className="space-y-1.5">
                    {previewData.query_plan.filters.map((f, idx) => (
                      <div key={idx} className="flex items-center gap-2 text-slate-200">
                        <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                        <span className="font-mono text-cyan-300 capitalize">{f.field.replace(/_/g, ' ')}:</span>
                        <strong>"{f.value}"</strong>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-slate-300 font-medium">All products in catalog</div>
                )}
              </div>

              <div className="space-y-2 p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
                <span className="text-[11px] font-bold text-slate-400 uppercase">Extracted Information:</span>
                <div className="flex flex-wrap gap-1.5">
                  {previewData.available_fields.map((f) => (
                    <span
                      key={f}
                      className="px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 text-[11px] font-semibold flex items-center gap-1"
                    >
                      <Check className="w-3 h-3 text-emerald-400" />
                      <span className="capitalize">{f.replace(/_/g, ' ')}</span>
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {previewData.unavailable_fields.length > 0 && (
              <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs">
                Some requested information isn't available in this catalog schema: {previewData.unavailable_fields.join(', ')}
              </div>
            )}
          </div>
        )}

        {errorMessage && (
          <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
            {errorMessage}
          </div>
        )}

        {/* Action Controls */}
        <div className="flex items-center justify-between pt-4 border-t border-slate-800">
          <button
            onClick={() => setActiveTab('understand')}
            className="px-4 py-2.5 rounded-xl text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors"
          >
            ← Back
          </button>

          <button
            onClick={handleStartAnalysis}
            className="px-8 py-3.5 rounded-xl text-sm font-bold bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition-all shadow-lg shadow-cyan-500/20 flex items-center gap-2 cursor-pointer"
          >
            <span>Start analysis</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
