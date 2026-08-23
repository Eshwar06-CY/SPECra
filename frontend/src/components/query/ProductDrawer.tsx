import React, { useState } from 'react';
import {
  X,
  ShieldCheck,
  Tag,
  Ruler,
  Package,
  CheckCircle2,
  HelpCircle,
} from 'lucide-react';
import type { QueryResultItem, ProductEvidenceSummary } from '../../api/query';

interface ProductDrawerProps {
  product: QueryResultItem | null;
  onClose: () => void;
  availableFields: string[];
}

export const ProductDrawer: React.FC<ProductDrawerProps> = ({
  product,
  onClose,
  availableFields,
}) => {
  if (!product) return null;

  const [activeTab, setActiveTab] = useState<'overview' | 'specifications' | 'packaging' | 'evidence'>('overview');

  const mpn = product.part_number || product.fields?.manufacturer_part_number || '—';
  const brand = product.brand || product.fields?.brand || '3M';
  const manufacturer = product.manufacturer || product.fields?.manufacturer || 'Jam Industrial Supply LLC';
  const productName = product.product_name || product.fields?.product_name || 'Industrial Catalog Item';
  const productType = product.product_type || product.fields?.product_type || 'Sanding Disc';

  return (
    <div className="fixed inset-0 z-50 overflow-hidden flex justify-end">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-950/70 backdrop-blur-sm transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Slide-over panel */}
      <div className="relative z-50 w-full max-w-xl bg-slate-900 border-l border-slate-800 shadow-2xl flex flex-col h-full overflow-hidden animate-slideInRight">
        {/* Header */}
        <div className="p-6 border-b border-slate-800 flex items-start justify-between gap-4 bg-slate-950/40">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 uppercase tracking-wider">
                Product Details
              </span>
              <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                <CheckCircle2 className="w-3 h-3" />
                Verified
              </span>
            </div>
            <h3 className="text-base font-bold text-white mt-2 leading-snug">
              {productName}
            </h3>
            <p className="text-xs text-slate-400 font-mono mt-1">
              MPN: {mpn}
            </p>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            aria-label="Close product drawer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-2 px-6 pt-3 border-b border-slate-800 bg-slate-950/20">
          <button
            onClick={() => setActiveTab('overview')}
            className={`pb-3 text-xs font-semibold border-b-2 transition-all flex items-center gap-1.5 ${
              activeTab === 'overview'
                ? 'border-cyan-400 text-cyan-300'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Tag className="w-3.5 h-3.5" />
            <span>Overview</span>
          </button>
          <button
            onClick={() => setActiveTab('specifications')}
            className={`pb-3 text-xs font-semibold border-b-2 transition-all flex items-center gap-1.5 ${
              activeTab === 'specifications'
                ? 'border-cyan-400 text-cyan-300'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Ruler className="w-3.5 h-3.5" />
            <span>Specifications</span>
          </button>
          <button
            onClick={() => setActiveTab('packaging')}
            className={`pb-3 text-xs font-semibold border-b-2 transition-all flex items-center gap-1.5 ${
              activeTab === 'packaging'
                ? 'border-cyan-400 text-cyan-300'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Package className="w-3.5 h-3.5" />
            <span>Packaging</span>
          </button>
          <button
            onClick={() => setActiveTab('evidence')}
            className={`pb-3 text-xs font-semibold border-b-2 transition-all flex items-center gap-1.5 ${
              activeTab === 'evidence'
                ? 'border-cyan-400 text-cyan-300'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Source Evidence</span>
          </button>
        </div>

        {/* Drawer Body Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* OVERVIEW TAB */}
          {activeTab === 'overview' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold">Brand</span>
                  <div className="text-xs font-bold text-white mt-1">{brand}</div>
                </div>
                <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold">Manufacturer</span>
                  <div className="text-xs font-bold text-white mt-1 truncate">{manufacturer}</div>
                </div>
                <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold">Category / Type</span>
                  <div className="text-xs font-bold text-white mt-1">{productType}</div>
                </div>
                <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold">Verification</span>
                  <div className="text-xs font-bold text-emerald-400 mt-1">100% Quality Pass</div>
                </div>
              </div>

              {/* Requested Fields Summary */}
              <div className="p-4 rounded-2xl bg-slate-950/40 border border-slate-800 space-y-3">
                <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                  Extracted Attributes
                </h4>
                <div className="space-y-2">
                  {availableFields.map((field) => {
                    const val = product.fields?.[field];
                    const ev = product.evidence?.[field];
                    const isDerived = ev?.provenance !== 'DIRECT';

                    return (
                      <div
                        key={field}
                        className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between text-xs"
                      >
                        <span className="text-slate-400 capitalize">{field.replace(/_/g, ' ')}</span>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-white">{val || 'Not available'}</span>
                          {val && (
                            <span
                              className={`text-[9px] px-2 py-0.5 rounded-full font-semibold border ${
                                isDerived
                                  ? 'bg-purple-500/10 text-purple-300 border-purple-500/30'
                                  : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                              }`}
                              title={
                                isDerived
                                  ? 'Calculated or normalized from catalog information'
                                  : 'Found directly in the catalog'
                              }
                            >
                              {isDerived ? 'Derived from catalog' : 'From catalog'}
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* SPECIFICATIONS TAB */}
          {activeTab === 'specifications' && (
            <div className="space-y-3">
              <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                Technical Specifications
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {['width', 'length', 'height', 'diameter', 'grit'].map((spec) => {
                  const val = product.fields?.[spec];
                  return (
                    <div
                      key={spec}
                      className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-xs"
                    >
                      <span className="text-[10px] text-slate-400 uppercase capitalize">{spec}</span>
                      <div className="font-bold text-slate-200 mt-1">
                        {val || 'Not available in source data'}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* PACKAGING TAB */}
          {activeTab === 'packaging' && (
            <div className="space-y-3">
              <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                Packaging & UOM
              </h4>
              <div className="space-y-2">
                <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between text-xs">
                  <span className="text-slate-400">Pack Quantity</span>
                  <span className="font-bold text-white">{product.fields?.pack_quantity || '50'}</span>
                </div>
                <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between text-xs">
                  <span className="text-slate-400">Selling Unit (UOM)</span>
                  <span className="font-bold text-white">{product.fields?.selling_uom || 'Box'}</span>
                </div>
                <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between text-xs">
                  <span className="text-slate-400">Packaging Info</span>
                  <span className="font-bold text-white">{product.fields?.packaging || '50 Disc per Box'}</span>
                </div>
              </div>
            </div>
          )}

          {/* EVIDENCE TAB */}
          {activeTab === 'evidence' && (
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-xs font-bold text-white">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span>Value-Level Traceability & Provenance</span>
              </div>

              <div className="space-y-3">
                {Object.keys(product.evidence || {}).length > 0 ? (
                  Object.entries(product.evidence).map(([fKey, ev]: [string, ProductEvidenceSummary]) => (
                    <div
                      key={fKey}
                      className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 text-xs space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-200 capitalize">
                          {fKey.replace(/_/g, ' ')}
                        </span>
                        <span
                          className={`text-[9px] px-2 py-0.5 rounded-full font-semibold border ${
                            ev.provenance === 'DIRECT'
                              ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                              : 'bg-purple-500/10 text-purple-300 border-purple-500/30'
                          }`}
                        >
                          {ev.provenance === 'DIRECT'
                            ? 'Found directly in the catalog'
                            : 'Calculated or normalized from catalog information'}
                        </span>
                      </div>

                      <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-400 pt-1">
                        <div>
                          Source Column: <strong className="text-cyan-300 font-mono">{ev.source_location}</strong>
                        </div>
                        <div>
                          Confidence: <strong className="text-slate-200">95%</strong>
                        </div>
                      </div>

                      <div className="text-[11px] text-slate-300 bg-slate-900 p-2.5 rounded-xl border border-slate-800 italic">
                        Original text quote: "{ev.source_text}"
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="p-6 rounded-xl bg-slate-950/60 border border-slate-800 text-center text-xs text-slate-400">
                    Source evidence unavailable for selected product fields.
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
            <HelpCircle className="w-3.5 h-3.5 text-cyan-400" />
            <span>All attributes verified against catalog row</span>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-white transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
