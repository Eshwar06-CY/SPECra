import React, { useState } from 'react';
import {
  Sparkles,
  Search,
  AlertTriangle,
  Zap,
} from 'lucide-react';
import type { ProductDetail } from '../types';
import { getProductIntelligence, enrichProduct } from '../services/api';

interface ProductIntelligenceViewProps {
  initialProductId?: string;
}

export const ProductIntelligenceView: React.FC<ProductIntelligenceViewProps> = ({
  initialProductId = 'b17feefb-5796-4b91-b487-dd6eb9bad9f7',
}) => {
  const [productIdInput, setProductIdInput] = useState(initialProductId);
  const [productDetail, setProductDetail] = useState<ProductDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [enriching, setEnriching] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [activeSubTab, setActiveSubTab] = useState<'attributes' | 'evidence' | 'enrichment' | 'raw'>('attributes');

  const handleFetchProduct = async (idToFetch?: string) => {
    const targetId = (idToFetch || productIdInput).trim();
    if (!targetId) return;

    setLoading(true);
    setErrorMsg(null);

    try {
      const data = await getProductIntelligence(targetId);
      setProductDetail(data);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Product not found or not yet processed.');
      setProductDetail(null);
    } finally {
      setLoading(false);
    }
  };

  const handleTriggerEnrichment = async () => {
    if (!productDetail) return;
    setEnriching(true);
    try {
      await enrichProduct(productDetail.product.id);
      await handleFetchProduct(productDetail.product.id);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to execute enrichment.');
    } finally {
      setEnriching(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Search & Action Bar */}
      <div className="glass-panel rounded-2xl p-6 border border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex-1 w-full flex items-center gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={productIdInput}
              onChange={(e) => setProductIdInput(e.target.value)}
              placeholder="Enter Product UUID (e.g. b17feefb-5796-4b91-b487-dd6eb9bad9f7)..."
              className="glass-input w-full pl-10 pr-4 py-2.5 rounded-xl text-sm font-mono text-slate-200 placeholder:text-slate-500"
            />
          </div>
          <button
            onClick={() => handleFetchProduct()}
            disabled={loading}
            className="px-5 py-2.5 rounded-xl text-sm font-semibold bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition-all shadow-md shadow-cyan-500/20 disabled:opacity-50 flex items-center gap-2"
          >
            <Sparkles className="w-4 h-4" />
            {loading ? 'Inspecting...' : 'Inspect Intelligence'}
          </button>
        </div>

        {productDetail && (
          <div className="flex items-center gap-2 w-full md:w-auto">
            <button
              onClick={handleTriggerEnrichment}
              disabled={enriching}
              className="w-full md:w-auto px-4 py-2.5 rounded-xl text-xs font-semibold bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 transition-all flex items-center justify-center gap-2"
            >
              <Zap className="w-3.5 h-3.5" />
              {enriching ? 'Enriching...' : 'Run Deterministic Enrichment'}
            </button>
          </div>
        )}
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {productDetail && (
        <div className="space-y-6">
          {/* Master Product Banner */}
          <div className="glass-panel rounded-2xl p-8 border border-slate-800">
            <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-1 rounded-md text-xs font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                    {productDetail.identity.product_type || productDetail.product.category || 'Industrial Product'}
                  </span>
                  {productDetail.identity.brand && (
                    <span className="px-2.5 py-1 rounded-md text-xs font-semibold bg-purple-500/10 text-purple-400 border border-purple-500/20">
                      Brand: {productDetail.identity.brand}
                    </span>
                  )}
                </div>
                <h2 className="text-2xl font-bold text-white tracking-tight">
                  {productDetail.identity.product_name || productDetail.product.product_name || 'Unnamed Product'}
                </h2>
                <div className="flex flex-wrap items-center gap-6 text-xs text-slate-400 pt-1">
                  <div>
                    <span className="text-slate-500">MPN / SKU:</span>{' '}
                    <span className="font-mono text-slate-200">
                      {productDetail.identity.manufacturer_part_number || productDetail.product.external_product_id || 'N/A'}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500">Manufacturer:</span>{' '}
                    <span className="text-slate-200">
                      {productDetail.identity.manufacturer || 'N/A'}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500">Product UUID:</span>{' '}
                    <span className="font-mono text-slate-400">{productDetail.product.id}</span>
                  </div>
                </div>
              </div>

              {/* Confidence & Specs Summary Metric */}
              <div className="flex items-center gap-4 bg-slate-900/60 p-4 rounded-xl border border-slate-800">
                <div className="text-center px-3 border-r border-slate-800">
                  <div className="text-2xl font-bold text-emerald-400">
                    {(productDetail.confidence * 100).toFixed(0)}%
                  </div>
                  <div className="text-xs text-slate-500 mt-0.5">Confidence</div>
                </div>
                <div className="text-center px-3">
                  <div className="text-2xl font-bold text-cyan-400">
                    {productDetail.total_attributes}
                  </div>
                  <div className="text-xs text-slate-500 mt-0.5">Specifications</div>
                </div>
              </div>
            </div>

            {/* Sub-Navigation Tabs */}
            <div className="flex items-center gap-2 border-b border-slate-800 mt-8 pt-2">
              {[
                { id: 'attributes', label: `Structured Attributes (${productDetail.attributes.length})` },
                { id: 'evidence', label: `Audit & Evidence Links (${productDetail.evidence.length})` },
                { id: 'raw', label: 'Raw Ingested Data' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveSubTab(tab.id as any)}
                  className={`pb-3 px-4 text-sm font-semibold border-b-2 transition-all ${
                    activeSubTab === tab.id
                      ? 'border-cyan-400 text-cyan-300'
                      : 'border-transparent text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {/* Sub-tab: Structured Attributes */}
          {activeSubTab === 'attributes' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {productDetail.attributes.map((attr) => (
                <div
                  key={attr.id}
                  className="glass-card rounded-xl p-5 border border-slate-800/80 space-y-3 relative group"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold tracking-wider text-cyan-400 uppercase">
                      {attr.name.replace('_', ' ')}
                    </span>
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${
                        attr.extraction_method === 'DETERMINISTIC'
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                          : 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20'
                      }`}
                    >
                      {attr.extraction_method}
                    </span>
                  </div>

                  <div className="text-lg font-bold text-white">
                    {attr.value}{' '}
                    {attr.unit && <span className="text-sm font-normal text-slate-400">{attr.unit}</span>}
                  </div>

                  {attr.normalized_value && attr.normalized_value !== attr.value && (
                    <div className="text-xs text-slate-400 flex items-center gap-1.5">
                      <span className="text-slate-500">Normalized:</span>
                      <span className="font-mono text-slate-300 font-semibold">{attr.normalized_value}</span>
                    </div>
                  )}

                  <div className="pt-2 border-t border-slate-800/50 flex items-center justify-between text-xs text-slate-400">
                    <span>Confidence: {(attr.confidence_score * 100).toFixed(0)}%</span>
                    <span className="text-slate-500">{attr.status}</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Sub-tab: Audit & Evidence */}
          {activeSubTab === 'evidence' && (
            <div className="glass-panel rounded-2xl p-6 border border-slate-800">
              <h3 className="text-base font-bold text-white mb-4">Evidence & Provenance Audit Trail</h3>
              <div className="space-y-3">
                {productDetail.evidence.map((ev) => (
                  <div
                    key={ev.id}
                    className="glass-card rounded-xl p-4 border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-white text-sm">
                          {ev.attribute_name || 'Attribute'}
                        </span>
                        <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                          {ev.source_location || 'Part_Desc'}
                        </span>
                        <span className="text-[11px] px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-mono">
                          {ev.provenance}
                        </span>
                      </div>
                      <div className="text-xs text-slate-300 font-mono bg-slate-950/60 px-3 py-1.5 rounded-lg border border-slate-800 inline-block">
                        source_text: "{ev.source_text}"
                      </div>
                    </div>
                    {ev.metadata?.notes && (
                      <div className="text-xs text-slate-400 max-w-md italic">
                        {ev.metadata.notes}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Sub-tab: Raw Data */}
          {activeSubTab === 'raw' && (
            <div className="glass-panel rounded-2xl p-6 border border-slate-800">
              <h3 className="text-base font-bold text-white mb-4">Ingested Raw Data Payload</h3>
              <pre className="text-xs font-mono bg-slate-950 p-4 rounded-xl border border-slate-800 overflow-x-auto text-cyan-300">
                {JSON.stringify(productDetail.product.raw_data, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
