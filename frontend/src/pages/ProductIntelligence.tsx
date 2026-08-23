import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  Search,
  Zap,
  AlertTriangle,
  Link,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import { getProductIntelligence } from '../api/intelligence';
import { enrichProduct, getProductEnrichment } from '../api/enrichment';
import { formatErrorMessage } from '../api/client';
import type { ProductDetailResponse, EnrichmentReportResponse } from '../types/api';

export const ProductIntelligence: React.FC = () => {
  const { selectedProductId, setSelectedProductId } = useApp();
  const [productIdInput, setProductIdInput] = useState<string>(selectedProductId || '');
  const [productData, setProductData] = useState<ProductDetailResponse | null>(null);
  const [enrichmentData, setEnrichmentData] = useState<EnrichmentReportResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [enriching, setEnriching] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [activeTabSub, setActiveTabSub] = useState<'attributes' | 'evidence' | 'enrichment' | 'raw'>('attributes');

  const fetchProduct = async (idToFetch: string) => {
    if (!idToFetch.trim()) return;
    setLoading(true);
    setErrorMessage(null);

    try {
      const data = await getProductIntelligence(idToFetch.trim());
      setProductData(data);
      setSelectedProductId(idToFetch.trim());

      // Attempt to load enrichment data if already executed
      try {
        const enrichReport = await getProductEnrichment(idToFetch.trim());
        setEnrichmentData(enrichReport);
      } catch {
        setEnrichmentData(null);
      }
    } catch (err: any) {
      setProductData(null);
      setErrorMessage(formatErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedProductId) {
      setProductIdInput(selectedProductId);
      fetchProduct(selectedProductId);
    }
  }, [selectedProductId]);

  const handleTriggerEnrichment = async () => {
    if (!productData) return;
    setEnriching(true);
    try {
      const res = await enrichProduct(productData.product.id);
      setEnrichmentData(res);
      await fetchProduct(productData.product.id);
      setActiveTabSub('enrichment');
    } catch (err: any) {
      setErrorMessage(formatErrorMessage(err));
    } finally {
      setEnriching(false);
    }
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Top Search & Filter Bar */}
      <div className="glass-panel rounded-2xl p-6 border border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex-1 w-full flex items-center gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={productIdInput}
              onChange={(e) => setProductIdInput(e.target.value)}
              placeholder="Enter Product UUID to inspect (e.g. b17feefb-5796-4b91-b487-dd6eb9bad9f7)..."
              className="glass-input w-full pl-10 pr-4 py-2.5 rounded-xl text-xs font-mono text-slate-200 placeholder:text-slate-500"
            />
          </div>
          <button
            onClick={() => fetchProduct(productIdInput)}
            disabled={loading}
            className="px-5 py-2.5 rounded-xl text-xs font-semibold bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition-all shadow-md shadow-cyan-500/20 disabled:opacity-50 flex items-center gap-2"
          >
            <Sparkles className="w-4 h-4" />
            <span>{loading ? 'Inspecting...' : 'Inspect Product'}</span>
          </button>
        </div>

        {productData && (
          <div className="flex items-center gap-2 w-full md:w-auto">
            <button
              onClick={handleTriggerEnrichment}
              disabled={enriching}
              className="w-full md:w-auto px-4 py-2.5 rounded-xl text-xs font-semibold bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 transition-all flex items-center justify-center gap-2"
            >
              <Zap className="w-3.5 h-3.5" />
              <span>{enriching ? 'Enriching...' : 'Run Deterministic Enrichment'}</span>
            </button>
          </div>
        )}
      </div>

      {errorMessage && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {productData && (
        <div className="space-y-6">
          {/* Master Identity Card */}
          <div className="glass-panel rounded-2xl p-8 border border-slate-800">
            <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
              <div className="space-y-2 max-w-3xl">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                    {productData.identity.product_type || productData.product.category || 'Product'}
                  </span>
                  {productData.identity.brand && (
                    <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-purple-500/10 text-purple-400 border border-purple-500/20">
                      Brand: {productData.identity.brand}
                    </span>
                  )}
                  {productData.identity.manufacturer && (
                    <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                      Mfr: {productData.identity.manufacturer}
                    </span>
                  )}
                </div>

                <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
                  {productData.identity.product_name || productData.product.product_name || 'Industrial Product'}
                </h2>

                <div className="flex flex-wrap items-center gap-6 text-xs text-slate-400 pt-1 font-mono">
                  <div>
                    <span className="text-slate-500 font-sans">MPN: </span>
                    <span className="text-slate-200">
                      {productData.identity.manufacturer_part_number || productData.product.external_product_id || 'N/A'}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 font-sans">UUID: </span>
                    <span className="text-slate-400">{productData.product.id}</span>
                  </div>
                </div>
              </div>

              {/* Confidence Metric Box */}
              <div className="flex items-center gap-4 bg-slate-900/80 p-4 rounded-2xl border border-slate-800">
                <div className="text-center px-4 border-r border-slate-800">
                  <div className="text-2xl font-bold text-emerald-400">
                    {(productData.confidence * 100).toFixed(0)}%
                  </div>
                  <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
                    Confidence
                  </div>
                </div>
                <div className="text-center px-4">
                  <div className="text-2xl font-bold text-cyan-400">
                    {productData.total_attributes}
                  </div>
                  <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
                    Attributes
                  </div>
                </div>
              </div>
            </div>

            {/* Navigation Tabs */}
            <div className="flex items-center gap-2 border-b border-slate-800 mt-8 pt-2">
              {[
                { id: 'attributes', label: `Dynamic Attributes (${productData.attributes.length})` },
                { id: 'evidence', label: `Traceable Evidence (${productData.evidence.length})` },
                { id: 'enrichment', label: `Deterministic Enrichment (${enrichmentData?.enrichments.length || 0})` },
                { id: 'raw', label: 'Raw Ingestion Payload' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTabSub(tab.id as any)}
                  className={`pb-3 px-4 text-xs font-semibold border-b-2 transition-all ${
                    activeTabSub === tab.id
                      ? 'border-cyan-400 text-cyan-300'
                      : 'border-transparent text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {/* Tab 1: Attributes Table */}
          {activeTabSub === 'attributes' && (
            <div className="glass-panel rounded-2xl p-6 border border-slate-800">
              <div className="overflow-x-auto rounded-xl border border-slate-800">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-900 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                    <tr>
                      <th className="py-3 px-4">Attribute Name</th>
                      <th className="py-3 px-4">Raw Extracted Value</th>
                      <th className="py-3 px-4">Normalized Value</th>
                      <th className="py-3 px-4">Unit</th>
                      <th className="py-3 px-4">Confidence</th>
                      <th className="py-3 px-4">Extraction Method</th>
                      <th className="py-3 px-4">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                    {productData.attributes.map((attr) => (
                      <tr key={attr.id} className="hover:bg-slate-900/40 transition-colors">
                        <td className="py-3 px-4 font-sans font-semibold text-white capitalize">
                          {attr.name.replace(/_/g, ' ')}
                        </td>
                        <td className="py-3 px-4 text-slate-200">{attr.value}</td>
                        <td className="py-3 px-4 text-cyan-300 font-bold">
                          {attr.normalized_value || attr.value}
                        </td>
                        <td className="py-3 px-4 text-slate-400">{attr.unit || '—'}</td>
                        <td className="py-3 px-4">
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                              attr.confidence_score >= 0.9
                                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                                : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                            }`}
                          >
                            {(attr.confidence_score * 100).toFixed(0)}%
                          </span>
                        </td>
                        <td className="py-3 px-4 font-sans">
                          <span
                            className={`text-[10px] px-2 py-0.5 rounded border ${
                              attr.extraction_method === 'DETERMINISTIC'
                                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                                : 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20'
                            }`}
                          >
                            {attr.extraction_method}
                          </span>
                        </td>
                        <td className="py-3 px-4 font-sans text-slate-400">{attr.status}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tab 2: Evidence & Provenance */}
          {activeTabSub === 'evidence' && (
            <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Link className="w-4 h-4 text-cyan-400" />
                  Attribute Traceability & Source Anchoring
                </h3>
                <span className="text-xs text-slate-500">Every value anchored to input evidence</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {productData.evidence.map((ev) => (
                  <div
                    key={ev.id}
                    className="glass-card rounded-xl p-4 border border-slate-800 space-y-2.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-white capitalize">
                        {ev.attribute_name?.replace(/_/g, ' ') || 'Attribute'}
                      </span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                        Provenance: {ev.provenance}
                      </span>
                    </div>

                    <div className="text-xs text-slate-400 space-y-1">
                      <div>
                        <span className="text-slate-500">Source Column: </span>
                        <span className="font-mono text-slate-300">{ev.source_location || 'Part_Desc'}</span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-cyan-300 font-mono text-[11px]">
                        "{ev.source_text}"
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tab 3: Deterministic Enrichment */}
          {activeTabSub === 'enrichment' && (
            <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-6">
              {!enrichmentData ? (
                <div className="text-center py-12 space-y-3">
                  <Zap className="w-8 h-8 text-slate-500 mx-auto" />
                  <div className="text-sm text-slate-300">No enrichment record for this product yet.</div>
                  <button
                    onClick={handleTriggerEnrichment}
                    disabled={enriching}
                    className="px-4 py-2 rounded-xl text-xs font-semibold bg-emerald-500 hover:bg-emerald-400 text-slate-950 transition-all"
                  >
                    Run Deterministic Enrichment Now
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-bold text-white">Enriched UniHack Fields</h3>
                      <p className="text-xs text-slate-400">
                        {enrichmentData.enriched_fields} fields populated • {enrichmentData.skipped_fields} fields blank (no evidence)
                      </p>
                    </div>
                  </div>

                  <div className="overflow-x-auto rounded-xl border border-slate-800">
                    <table className="w-full text-left text-xs text-slate-300">
                      <thead className="bg-slate-900 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                        <tr>
                          <th className="py-3 px-4">UniHack Field</th>
                          <th className="py-3 px-4">Enriched Value</th>
                          <th className="py-3 px-4">Method</th>
                          <th className="py-3 px-4">Provenance</th>
                          <th className="py-3 px-4">Source Location</th>
                          <th className="py-3 px-4">Evidence Text</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                        {enrichmentData.enrichments.map((en, idx) => (
                          <tr key={idx} className="hover:bg-slate-900/40 transition-colors">
                            <td className="py-3 px-4 font-sans font-semibold text-white">
                              {en.field}
                            </td>
                            <td className="py-3 px-4 text-emerald-300 font-bold">{en.value}</td>
                            <td className="py-3 px-4 font-sans">
                              <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                                {en.method}
                              </span>
                            </td>
                            <td className="py-3 px-4">
                              <span
                                className={`text-[10px] px-2 py-0.5 rounded-full border ${
                                  en.provenance === 'DIRECT'
                                    ? 'bg-blue-500/10 text-blue-300 border-blue-500/20'
                                    : 'bg-indigo-500/10 text-indigo-300 border-indigo-500/20'
                                }`}
                              >
                                {en.provenance}
                              </span>
                            </td>
                            <td className="py-3 px-4 text-slate-400">{en.source_location || '—'}</td>
                            <td className="py-3 px-4 text-cyan-400 truncate max-w-xs">
                              "{en.source_text}"
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Tab 4: Raw Ingestion Payload */}
          {activeTabSub === 'raw' && (
            <div className="glass-panel rounded-2xl p-6 border border-slate-800">
              <h3 className="text-sm font-bold text-white mb-3">Raw Record JSON</h3>
              <pre className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-cyan-300 text-xs font-mono overflow-x-auto">
                {JSON.stringify(productData.product.raw_data, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
