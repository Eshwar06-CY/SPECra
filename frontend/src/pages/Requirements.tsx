import React, { useState } from 'react';
import {
  Sparkles,
  CheckCircle2,
  Edit3,
  Check,
  AlertTriangle,
  HelpCircle,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import { previewProductQuery, type QueryPreviewResponse } from '../api/query';
import { WorkflowProgress } from '../components/layout/WorkflowProgress';

export const Requirements: React.FC = () => {
  const { selectedJobId, setActiveTab, setActiveQuery } = useApp();
  const [customPrompt, setCustomPrompt] = useState<string>(
    'Find all 3M sanding products and give me the product name, manufacturer, dimensions and packaging quantity.'
  );
  const [previewData, setPreviewData] = useState<QueryPreviewResponse | null>(null);
  const [previewing, setPreviewing] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const examplePrompts = [
    'Find all products from 3M',
    'Show sanding products with their dimensions',
    'Find products sold in packs of 50',
    'Give me manufacturer, brand and MPN for all products',
  ];

  const handleApplyExample = (prompt: string) => {
    setCustomPrompt(prompt);
    setPreviewData(null);
    setErrorMessage(null);
  };

  const handleUnderstandRequest = async () => {
    if (!selectedJobId) {
      setErrorMessage('Please upload or select a catalog first.');
      return;
    }
    if (!customPrompt.trim()) {
      setErrorMessage('Please describe the products and information you need.');
      return;
    }

    setPreviewing(true);
    setErrorMessage(null);
    try {
      const res = await previewProductQuery(selectedJobId, customPrompt.trim());
      setPreviewData(res);
    } catch (err: any) {
      setErrorMessage(
        "We couldn't understand that request. Try describing the products and information you need."
      );
    } finally {
      setPreviewing(false);
    }
  };

  const handleConfirmAndRunAnalysis = () => {
    if (customPrompt.trim()) {
      setActiveQuery(customPrompt.trim());
    } else {
      setActiveQuery(null);
    }
    setActiveTab('process');
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-12">
      {/* Workflow Stepper */}
      <WorkflowProgress currentTab="requirements" completedTabs={['upload', 'understand']} />

      {/* Main Requirement Card */}
      <div className="specra-panel rounded-3xl p-8 border border-slate-800 space-y-8">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">
            Tell SPECra what you need
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Describe the products and information you're looking for in plain language.
          </p>
        </div>

        {/* Input Box */}
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <label className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-cyan-400" />
              <span>Natural Language Request</span>
            </label>
            <span className="text-[11px] text-cyan-400/80 font-mono">AI Query Planner</span>
          </div>

          <div className="relative">
            <textarea
              rows={3}
              value={customPrompt}
              onChange={(e) => {
                setCustomPrompt(e.target.value);
                setPreviewData(null);
              }}
              placeholder="Find all 3M sanding products and show me the product name, manufacturer, brand, dimensions and packaging quantity."
              className="specra-input w-full px-4 py-3 rounded-xl text-xs text-white placeholder:text-slate-500 resize-none font-sans"
            />
          </div>

          {/* Example Prompts */}
          <div className="space-y-2 pt-1">
            <span className="text-[11px] text-slate-400 font-semibold uppercase tracking-wider flex items-center gap-1.5">
              <HelpCircle className="w-3.5 h-3.5 text-slate-500" />
              <span>Try one of these examples:</span>
            </span>
            <div className="flex flex-wrap gap-2">
              {examplePrompts.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  onClick={() => handleApplyExample(prompt)}
                  className="px-3 py-1.5 rounded-xl text-xs font-medium bg-slate-950/80 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-800 hover:border-slate-700 transition-all cursor-pointer text-left"
                >
                  "{prompt}"
                </button>
              ))}
            </div>
          </div>

          {/* Understand Request Button */}
          {!previewData && (
            <div className="flex justify-end pt-2">
              <button
                onClick={handleUnderstandRequest}
                disabled={previewing || !customPrompt.trim()}
                className="px-6 py-3 rounded-xl text-xs font-bold bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition-all disabled:opacity-50 flex items-center gap-2 shadow-lg shadow-cyan-500/20 cursor-pointer"
              >
                {previewing ? (
                  <div className="w-3.5 h-3.5 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Sparkles className="w-3.5 h-3.5" />
                )}
                <span>Understand Request</span>
              </button>
            </div>
          )}
        </div>

        {/* Human Confirmation / Review Interpretation Card */}
        {previewData && (
          <div className="p-6 rounded-2xl bg-cyan-950/20 border border-cyan-500/40 space-y-5 animate-fadeIn">
            <div className="flex items-center justify-between border-b border-cyan-500/20 pb-3">
              <h4 className="text-sm font-bold text-white flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-cyan-400" />
                <span>Here's what I understood</span>
              </h4>
              <button
                onClick={() => setPreviewData(null)}
                className="text-xs text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1 cursor-pointer"
              >
                <Edit3 className="w-3.5 h-3.5" />
                <span>Edit Request</span>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              {/* Filtered Products / Scope */}
              <div className="space-y-2 p-4 rounded-xl bg-slate-950/70 border border-slate-800">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                  Targeted Products:
                </span>
                {previewData.query_plan.filters.length > 0 ? (
                  <div className="space-y-2">
                    {previewData.query_plan.filters.map((f, idx) => (
                      <div key={idx} className="flex items-center gap-2 text-slate-200">
                        <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                        <span className="text-slate-400 capitalize">{f.field.replace(/_/g, ' ')} &rarr;</span>
                        <strong className="text-cyan-300 font-semibold">{f.value}</strong>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-slate-300 font-medium flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                    <span>All products in uploaded catalog</span>
                  </div>
                )}
              </div>

              {/* Information You'll Receive */}
              <div className="space-y-2 p-4 rounded-xl bg-slate-950/70 border border-slate-800">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                  Information you'll receive:
                </span>
                <div className="space-y-1.5">
                  {['Product Name', 'Manufacturer', 'Brand', ...previewData.available_fields.filter(f => !['product_name', 'manufacturer', 'brand'].includes(f))].map((f) => (
                    <div key={f} className="flex items-center gap-2 text-emerald-300 font-medium">
                      <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                      <span className="capitalize">{f.replace(/_/g, ' ')}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Unavailable Information Alert */}
            {previewData.unavailable_fields.length > 0 && (
              <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-200 text-xs space-y-1">
                <div className="font-semibold flex items-center gap-1.5 text-amber-300">
                  <AlertTriangle className="w-4 h-4 shrink-0" />
                  <span>Some requested information isn't available in this catalog.</span>
                </div>
                <p className="text-slate-300 text-[11px] pl-5">
                  &bull; {previewData.unavailable_fields.map(f => f.replace(/_/g, ' ')).join(', ')} was not found in the uploaded catalog.
                </p>
              </div>
            )}

            {/* Confirmation Buttons */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-3 border-t border-cyan-500/20">
              <button
                type="button"
                onClick={() => setPreviewData(null)}
                className="w-full sm:w-auto px-4 py-2.5 rounded-xl text-xs font-semibold text-slate-400 hover:text-white bg-slate-900 border border-slate-800 transition-colors cursor-pointer"
              >
                &larr; Edit Request
              </button>

              <button
                type="button"
                onClick={handleConfirmAndRunAnalysis}
                className="w-full sm:w-auto px-8 py-3 rounded-xl text-xs font-bold bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition-all shadow-lg shadow-cyan-500/20 flex items-center justify-center gap-2 cursor-pointer"
              >
                <span>Looks Good &mdash; Run Analysis &rarr;</span>
              </button>
            </div>
          </div>
        )}

        {errorMessage && (
          <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
            {errorMessage}
          </div>
        )}

        {/* Back Button */}
        {!previewData && (
          <div className="flex items-center justify-between pt-4 border-t border-slate-800">
            <button
              onClick={() => setActiveTab('understand')}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
            >
              &larr; Back to Catalog Structure
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
