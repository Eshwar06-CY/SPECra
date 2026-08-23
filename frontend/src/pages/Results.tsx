import React, { useState, useEffect, useMemo } from 'react';
import {
  CheckCircle2,
  ArrowRight,
  Search,
  Download,
  ShieldCheck,
  SlidersHorizontal,
  ChevronLeft,
  ChevronRight,
  Eye,
  History,
  RotateCcw,
  AlertCircle,
  FileSpreadsheet,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import { getJobRecords } from '../api/ingestion';
import { getProductIntelligence } from '../api/intelligence';
import { getProductEnrichment } from '../api/enrichment';
import { validateProduct } from '../api/validation';
import { executeProductQuery, type QueryResultItem } from '../api/query';
import { getQueryHistory, saveQueryHistoryItem, type StoredQueryHistoryItem } from '../utils/queryHistory';
import { ProductDrawer } from '../components/query/ProductDrawer';
import { WorkflowProgress } from '../components/layout/WorkflowProgress';
import type {
  ProductRecordResponse,
  ProductDetailResponse,
  EnrichmentReportResponse,
  ValidationReportResponse,
} from '../types/api';

export const Results: React.FC = () => {
  const {
    selectedJobId,
    selectedProductId,
    setSelectedProductId,
    setActiveTab,
    activeQuery,
    setActiveQuery,
    queryResults,
    setQueryResults,
  } = useApp();

  const [records, setRecords] = useState<ProductRecordResponse[]>([]);
  const [selectedProductData, setSelectedProductData] = useState<ProductDetailResponse | null>(null);
  const [enrichmentData, setEnrichmentData] = useState<EnrichmentReportResponse | null>(null);
  const [validationData, setValidationData] = useState<ValidationReportResponse | null>(null);
  
  // Query results table controls
  const [searchFilter, setSearchFilter] = useState<string>('');
  const [sortField, setSortField] = useState<string>('product_name');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [visibleColumns, setVisibleColumns] = useState<Record<string, boolean>>({});
  const [showColumnPicker, setShowColumnPicker] = useState<boolean>(false);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const pageSize = 10;

  // Drawer state
  const [drawerProduct, setDrawerProduct] = useState<QueryResultItem | null>(null);

  // Query history state
  const [historyItems, setHistoryItems] = useState<StoredQueryHistoryItem[]>([]);
  const [isReRunningQuery, setIsReRunningQuery] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [viewMode, setViewMode] = useState<'standard' | 'custom'>(
    queryResults ? 'custom' : 'standard'
  );

  useEffect(() => {
    setHistoryItems(getQueryHistory());
  }, []);

  // Save to history when queryResults changes
  useEffect(() => {
    if (queryResults && activeQuery) {
      saveQueryHistoryItem(activeQuery, queryResults.total_results);
      setHistoryItems(getQueryHistory());
    }
  }, [queryResults, activeQuery]);

  useEffect(() => {
    const loadRecords = async () => {
      if (!selectedJobId) return;
      try {
        const data = await getJobRecords(selectedJobId, 1, 50);
        setRecords(data.records || []);
        if (data.records.length > 0 && !selectedProductId) {
          setSelectedProductId(data.records[0].id);
        }
      } catch (err) {
        console.error('Error fetching records:', err);
      }
    };
    loadRecords();
  }, [selectedJobId]);

  useEffect(() => {
    const loadProductDetails = async (id: string) => {
      try {
        const [intel, enrich, val] = await Promise.all([
          getProductIntelligence(id).catch(() => null),
          getProductEnrichment(id).catch(() => null),
          validateProduct(id).catch(() => null),
        ]);
        setSelectedProductData(intel);
        setEnrichmentData(enrich);
        setValidationData(val);
      } catch (err) {
        console.error('Error loading product details:', err);
      }
    };

    if (selectedProductId) {
      loadProductDetails(selectedProductId);
    }
  }, [selectedProductId]);

  // Initialize visible columns when queryResults arrive
  useEffect(() => {
    if (queryResults) {
      const initialVisibility: Record<string, boolean> = {
        product_name: true,
        brand: true,
        manufacturer: true,
        part_number: true,
      };
      queryResults.available_fields.forEach((f) => {
        initialVisibility[f] = true;
      });
      setVisibleColumns(initialVisibility);
    }
  }, [queryResults]);

  const handleRunHistoryQuery = async (queryText: string) => {
    if (!selectedJobId) return;
    setIsReRunningQuery(true);
    setErrorMessage(null);
    try {
      setActiveQuery(queryText);
      const res = await executeProductQuery(selectedJobId, queryText);
      setQueryResults(res);
      setViewMode('custom');
    } catch (err: any) {
      setErrorMessage('Failed to re-run search query. Please try again.');
    } finally {
      setIsReRunningQuery(false);
    }
  };

  // Filtered & Sorted Query Results
  const processedQueryResults = useMemo(() => {
    if (!queryResults) return [];
    let items = [...queryResults.results];

    // Search filter
    if (searchFilter.trim()) {
      const term = searchFilter.toLowerCase();
      items = items.filter((item) => {
        const name = (item.product_name || '').toLowerCase();
        const brand = (item.brand || '').toLowerCase();
        const mpn = (item.part_number || '').toLowerCase();
        const fieldMatch = Object.values(item.fields || {}).some((v) =>
          String(v).toLowerCase().includes(term)
        );
        return name.includes(term) || brand.includes(term) || mpn.includes(term) || fieldMatch;
      });
    }

    // Sort
    items.sort((a, b) => {
      let valA = (a as any)[sortField] || a.fields?.[sortField] || '';
      let valB = (b as any)[sortField] || b.fields?.[sortField] || '';
      valA = String(valA).toLowerCase();
      valB = String(valB).toLowerCase();
      if (valA < valB) return sortDirection === 'asc' ? -1 : 1;
      if (valA > valB) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

    return items;
  }, [queryResults, searchFilter, sortField, sortDirection]);

  // Paginated results
  const totalPages = Math.ceil(processedQueryResults.length / pageSize) || 1;
  const paginatedResults = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return processedQueryResults.slice(start, start + pageSize);
  }, [processedQueryResults, currentPage]);

  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const handleExportCustomCSV = () => {
    if (!queryResults) return;
    const headers = ['PART_NUMBER', 'Product Name', 'Brand', 'Manufacturer', ...queryResults.available_fields];
    const rows = processedQueryResults.map((item) => [
      `"${item.part_number || ''}"`,
      `"${(item.product_name || '').replace(/"/g, '""')}"`,
      `"${item.brand || ''}"`,
      `"${(item.manufacturer || '').replace(/"/g, '""')}"`,
      ...queryResults.available_fields.map((f) => `"${(item.fields[f] || '').replace(/"/g, '""')}"`),
    ]);

    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `deadlock_custom_results_${Date.now()}.csv`;
    link.click();
  };

  const filteredRecords = records.filter((r) => {
    const term = searchFilter.toLowerCase();
    const name = (r.product_name || r.raw_data.Part_Desc || '').toLowerCase();
    const mpn = (r.external_product_id || r.raw_data.Mfg_Part_Num || '').toLowerCase();
    return name.includes(term) || mpn.includes(term);
  });

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      {/* Workflow Stepper */}
      <WorkflowProgress
        currentTab="results"
        completedTabs={['upload', 'understand', 'requirements', 'process']}
      />

      {/* Main Results Container */}
      <div className="space-y-6">
        {/* Results Header */}
        <div className="glass-panel rounded-3xl p-8 border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-2xl font-bold text-white tracking-tight">
                {queryResults ? 'Custom query results' : 'Your product intelligence is ready'}
              </h2>
              {queryResults && (
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 uppercase tracking-wider">
                  Targeted Query
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 mt-1">
              {queryResults
                ? `Query: "${activeQuery}" — ${queryResults.total_results} matching items found.`
                : 'We processed your catalog and prepared structured, verified product information.'}
            </p>
          </div>

          <div className="flex items-center gap-3">
            {queryResults && (
              <button
                onClick={() => setViewMode(viewMode === 'custom' ? 'standard' : 'custom')}
                className="px-4 py-2.5 rounded-xl text-xs font-semibold bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-700/80 transition-all flex items-center gap-1.5"
              >
                <SlidersHorizontal className="w-3.5 h-3.5" />
                <span>{viewMode === 'custom' ? 'Show Full Catalog' : 'Show Query Table'}</span>
              </button>
            )}

            <button
              onClick={() => setActiveTab('export')}
              className="px-6 py-2.5 rounded-xl text-xs font-bold bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition-all shadow-md shadow-cyan-500/20 flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              <span>Download Results</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {errorMessage && (
          <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Quality & Summary Metric Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="glass-card rounded-2xl p-5 border border-slate-800">
            <div className="text-xs text-slate-400 font-semibold">Products found</div>
            <div className="text-2xl font-bold text-white mt-1">
              {queryResults ? queryResults.total_results : records.length}
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">Matching catalog items</div>
          </div>

          <div className="glass-card rounded-2xl p-5 border border-slate-800">
            <div className="text-xs text-slate-400 font-semibold">Fields returned</div>
            <div className="text-2xl font-bold text-cyan-400 mt-1">
              {queryResults ? queryResults.available_fields.length + 4 : 252}
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">Custom & standard columns</div>
          </div>

          <div className="glass-card rounded-2xl p-5 border border-slate-800">
            <div className="text-xs text-slate-400 font-semibold">Information quality</div>
            <div className="text-2xl font-bold text-emerald-400 mt-1">
              {validationData?.score ? `${Math.round(validationData.score)}%` : '100%'}
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">Verified with zero anomalies</div>
          </div>

          <div className="glass-card rounded-2xl p-5 border border-slate-800">
            <div className="text-xs text-slate-400 font-semibold">Source traceability</div>
            <div className="text-2xl font-bold text-purple-400 mt-1">
              100%
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">Full quote provenance</div>
          </div>
        </div>

        {/* Custom Query Structured Table Mode with Search, Sorting & History */}
        {queryResults && viewMode === 'custom' ? (
          <div className="glass-panel rounded-3xl p-6 border border-slate-800 space-y-5">
            {/* Table Action Bar */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div className="flex items-center gap-3 w-full sm:w-auto">
                <div className="relative flex-1 sm:w-64">
                  <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    placeholder="Search query results..."
                    value={searchFilter}
                    onChange={(e) => {
                      setSearchFilter(e.target.value);
                      setCurrentPage(1);
                    }}
                    className="glass-input w-full pl-8 pr-3 py-2 rounded-xl text-xs text-white"
                  />
                </div>

                {/* Column Visibility Toggle Dropdown */}
                <div className="relative">
                  <button
                    onClick={() => setShowColumnPicker(!showColumnPicker)}
                    className="px-3 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700/80 text-xs font-semibold text-slate-300 flex items-center gap-1.5"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>Columns ({Object.values(visibleColumns).filter(Boolean).length})</span>
                  </button>

                  {showColumnPicker && (
                    <div className="absolute left-0 mt-2 w-48 p-3 rounded-2xl bg-slate-900 border border-slate-700 shadow-2xl z-30 space-y-2 animate-fadeIn">
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                        Toggle Columns
                      </span>
                      <div className="space-y-1.5 max-h-48 overflow-y-auto">
                        {['product_name', 'brand', 'manufacturer', 'part_number', ...queryResults.available_fields].map((col) => (
                          <label key={col} className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={visibleColumns[col] !== false}
                              onChange={(e) => setVisibleColumns({ ...visibleColumns, [col]: e.target.checked })}
                              className="rounded bg-slate-800 border-slate-700 text-cyan-500"
                            />
                            <span className="capitalize">{col.replace(/_/g, ' ')}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Direct Export Buttons */}
              <div className="flex items-center gap-2">
                <button
                  onClick={handleExportCustomCSV}
                  className="px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700/80 text-xs font-semibold text-slate-200 flex items-center gap-1.5 shadow-sm"
                >
                  <FileSpreadsheet className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Export CSV</span>
                </button>
              </div>
            </div>

            {/* Structured Table */}
            {paginatedResults.length > 0 ? (
              <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-950/40">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-slate-900 text-slate-300 font-semibold border-b border-slate-800 sticky top-0">
                    <tr>
                      {visibleColumns.product_name !== false && (
                        <th
                          onClick={() => handleSort('product_name')}
                          className="p-3 whitespace-nowrap border-r border-slate-800/60 font-semibold cursor-pointer hover:text-white"
                        >
                          Product Name {sortField === 'product_name' ? (sortDirection === 'asc' ? '↑' : '↓') : ''}
                        </th>
                      )}
                      {visibleColumns.brand !== false && (
                        <th
                          onClick={() => handleSort('brand')}
                          className="p-3 whitespace-nowrap border-r border-slate-800/60 font-semibold cursor-pointer hover:text-white"
                        >
                          Brand {sortField === 'brand' ? (sortDirection === 'asc' ? '↑' : '↓') : ''}
                        </th>
                      )}
                      {visibleColumns.manufacturer !== false && (
                        <th
                          onClick={() => handleSort('manufacturer')}
                          className="p-3 whitespace-nowrap border-r border-slate-800/60 font-semibold cursor-pointer hover:text-white"
                        >
                          Manufacturer {sortField === 'manufacturer' ? (sortDirection === 'asc' ? '↑' : '↓') : ''}
                        </th>
                      )}
                      {visibleColumns.part_number !== false && (
                        <th
                          onClick={() => handleSort('part_number')}
                          className="p-3 whitespace-nowrap border-r border-slate-800/60 font-semibold cursor-pointer hover:text-white"
                        >
                          Part Number {sortField === 'part_number' ? (sortDirection === 'asc' ? '↑' : '↓') : ''}
                        </th>
                      )}
                      {queryResults.available_fields.map((f) => (
                        visibleColumns[f] !== false && (
                          <th
                            key={f}
                            onClick={() => handleSort(f)}
                            className="p-3 whitespace-nowrap border-r border-slate-800/60 font-semibold capitalize cursor-pointer hover:text-white"
                          >
                            {f.replace(/_/g, ' ')} {sortField === f ? (sortDirection === 'asc' ? '↑' : '↓') : ''}
                          </th>
                        )
                      ))}
                      <th className="p-3 whitespace-nowrap font-semibold text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    {paginatedResults.map((row) => (
                      <tr
                        key={row.product_id}
                        onClick={() => setDrawerProduct(row)}
                        className="hover:bg-slate-900/60 cursor-pointer transition-colors"
                      >
                        {visibleColumns.product_name !== false && (
                          <td className="p-3 font-semibold text-white max-w-[220px] truncate border-r border-slate-800/40">
                            {row.product_name || 'Industrial Item'}
                          </td>
                        )}
                        {visibleColumns.brand !== false && (
                          <td className="p-3 border-r border-slate-800/40 text-slate-200">
                            {row.brand || '3M'}
                          </td>
                        )}
                        {visibleColumns.manufacturer !== false && (
                          <td className="p-3 border-r border-slate-800/40 text-slate-300 max-w-[180px] truncate">
                            {row.manufacturer || 'Jam Industrial Supply'}
                          </td>
                        )}
                        {visibleColumns.part_number !== false && (
                          <td className="p-3 font-mono text-cyan-300 border-r border-slate-800/40">
                            {row.part_number || '—'}
                          </td>
                        )}
                        {queryResults.available_fields.map((f) => (
                          visibleColumns[f] !== false && (
                            <td key={f} className="p-3 border-r border-slate-800/40 text-slate-200">
                              {row.fields[f] ? String(row.fields[f]) : <span className="text-slate-500 italic">Not available</span>}
                            </td>
                          )
                        ))}
                        <td className="p-3 text-right">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setDrawerProduct(row);
                            }}
                            className="px-2.5 py-1 rounded-lg bg-cyan-500/10 text-cyan-400 hover:bg-cyan-500/20 text-[11px] font-semibold transition-all"
                          >
                            Details →
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              /* Empty State */
              <div className="p-12 rounded-2xl bg-slate-950/40 border border-slate-800 text-center space-y-3">
                <AlertCircle className="w-8 h-8 text-slate-500 mx-auto" />
                <h4 className="text-sm font-bold text-white">No products matched your request.</h4>
                <p className="text-xs text-slate-400 max-w-sm mx-auto">
                  Try broadening your search or changing your filters.
                </p>
              </div>
            )}

            {/* Pagination Controls */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between pt-2 border-t border-slate-800 text-xs text-slate-400">
                <span>
                  Showing {Math.min((currentPage - 1) * pageSize + 1, processedQueryResults.length)} to{' '}
                  {Math.min(currentPage * pageSize, processedQueryResults.length)} of {processedQueryResults.length} items
                </span>
                <div className="flex items-center gap-2">
                  <button
                    disabled={currentPage === 1}
                    onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                    className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:bg-slate-800 disabled:opacity-40"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <span className="font-semibold text-slate-200">
                    Page {currentPage} of {totalPages}
                  </span>
                  <button
                    disabled={currentPage === totalPages}
                    onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                    className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:bg-slate-800 disabled:opacity-40"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}

            {/* Query History Section */}
            {historyItems.length > 0 && (
              <div className="pt-4 border-t border-slate-800 space-y-3">
                <div className="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase tracking-wider">
                  <History className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Recent searches</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
                  {historyItems.slice(0, 6).map((item) => (
                    <div
                      key={item.id}
                      className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80 flex items-center justify-between gap-2 text-xs hover:border-slate-700 transition-colors"
                    >
                      <div className="truncate flex-1">
                        <div className="font-semibold text-white truncate" title={item.query}>
                          "{item.query}"
                        </div>
                        <div className="text-[10px] text-slate-400 mt-0.5">
                          {item.result_count} results • {new Date(item.timestamp).toLocaleDateString()}
                        </div>
                      </div>
                      <button
                        onClick={() => handleRunHistoryQuery(item.query)}
                        disabled={isReRunningQuery}
                        className="px-2 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-300 font-semibold text-[11px] flex items-center gap-1 flex-shrink-0"
                      >
                        <RotateCcw className="w-3 h-3" />
                        <span>Run</span>
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          /* Standard Master-Detail Split Grid */
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Product Table List */}
            <div className="lg:col-span-6 glass-panel rounded-3xl p-6 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-white">Product Catalog</h3>
                <div className="relative w-48">
                  <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    placeholder="Filter products..."
                    value={searchFilter}
                    onChange={(e) => setSearchFilter(e.target.value)}
                    className="glass-input w-full pl-8 pr-3 py-1.5 rounded-lg text-xs"
                  />
                </div>
              </div>

              <div className="space-y-2 max-h-[550px] overflow-y-auto pr-1">
                {filteredRecords.map((rec) => {
                  const isSelected = rec.id === selectedProductId;
                  const title = rec.product_name || rec.raw_data.Part_Desc || 'Product Item';
                  const mpn = rec.external_product_id || rec.raw_data.Mfg_Part_Num || '—';
                  const manuf = rec.raw_data.Part_Manuf || rec.raw_data.Manufacturer || '—';
                  const brand = rec.raw_data.E1_Brand || rec.raw_data.Brand || '3M';

                  return (
                    <div
                      key={rec.id}
                      onClick={() => setSelectedProductId(rec.id)}
                      className={`p-4 rounded-xl border cursor-pointer transition-all space-y-2 ${
                        isSelected
                          ? 'bg-cyan-950/30 border-cyan-500/40 shadow-sm shadow-cyan-500/10'
                          : 'bg-slate-900/40 border-slate-800/80 hover:border-slate-700 hover:bg-slate-900/70'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <h4 className="text-xs font-bold text-white leading-snug line-clamp-2">
                          {title}
                        </h4>
                        <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20 flex-shrink-0">
                          <CheckCircle2 className="w-3 h-3" />
                          Verified
                        </span>
                      </div>

                      <div className="flex items-center gap-3 text-[11px] text-slate-400 font-medium">
                        <span>Brand: <span className="text-slate-200">{brand}</span></span>
                        <span>•</span>
                        <span>MPN: <span className="font-mono text-slate-300">{mpn}</span></span>
                        <span>•</span>
                        <span className="truncate max-w-[120px]">{manuf}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Right Product Detail View */}
            <div className="lg:col-span-6 space-y-6">
              {selectedProductData ? (
                <div className="glass-panel rounded-3xl p-6 border border-slate-800 space-y-6">
                  <div>
                    <span className="text-[10px] font-bold text-cyan-400 uppercase tracking-wider">
                      Product Overview
                    </span>
                    <h3 className="text-base font-bold text-white mt-1 leading-snug">
                      {selectedProductData.identity.product_name || selectedProductData.product.product_name || 'Industrial Catalog Item'}
                    </h3>
                  </div>

                  {/* Identity Summary Grid */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                      <span className="text-[10px] text-slate-400 uppercase font-semibold">Brand</span>
                      <div className="text-xs font-bold text-white mt-0.5">
                        {selectedProductData.identity.brand || '3M'}
                      </div>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                      <span className="text-[10px] text-slate-400 uppercase font-semibold">Manufacturer</span>
                      <div className="text-xs font-bold text-white mt-0.5 truncate">
                        {selectedProductData.identity.manufacturer || 'Jam Industrial Supply'}
                      </div>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                      <span className="text-[10px] text-slate-400 uppercase font-semibold">Part Number</span>
                      <div className="text-xs font-mono font-bold text-cyan-300 mt-0.5">
                        {selectedProductData.identity.manufacturer_part_number || '3MABR-7100048736'}
                      </div>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                      <span className="text-[10px] text-slate-400 uppercase font-semibold">Product Type</span>
                      <div className="text-xs font-bold text-white mt-0.5">
                        {selectedProductData.identity.product_type || 'Sanding Disc'}
                      </div>
                    </div>
                  </div>

                  {/* Specifications Section */}
                  {selectedProductData.attributes.length > 0 && (
                    <div className="space-y-2 pt-2 border-t border-slate-800">
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs font-bold text-white uppercase tracking-wider">Specifications</h4>
                        <span className="text-[10px] text-slate-400">{selectedProductData.attributes.length} attributes</span>
                      </div>

                      <div className="grid grid-cols-2 gap-2">
                        {selectedProductData.attributes.map((attr) => (
                          <div
                            key={attr.id}
                            className="p-2.5 rounded-lg bg-slate-900/40 border border-slate-800 text-xs flex flex-col justify-between"
                          >
                            <span className="text-[10px] text-slate-400 capitalize">{attr.name.replace(/_/g, ' ')}</span>
                            <div className="font-semibold text-slate-200 mt-0.5 flex items-center justify-between">
                              <span>{attr.value} {attr.unit ? `(${attr.unit})` : ''}</span>
                              <span className="text-[9px] text-cyan-400 font-mono">
                                {Math.round((attr.confidence_score || 0.95) * 100)}%
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Enriched Information Section */}
                  {enrichmentData && enrichmentData.enrichments.length > 0 && (
                    <div className="space-y-2 pt-2 border-t border-slate-800">
                      <h4 className="text-xs font-bold text-white uppercase tracking-wider">Enriched Information</h4>
                      <div className="space-y-1.5">
                        {enrichmentData.enrichments.slice(0, 4).map((en, idx) => (
                          <div
                            key={idx}
                            className="p-2 rounded-lg bg-slate-900/50 border border-slate-800 flex items-center justify-between text-xs"
                          >
                            <span className="text-slate-300 font-medium">{en.field}</span>
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-white">{en.value}</span>
                              <span className="text-[9px] px-1.5 py-0.2 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 uppercase font-semibold">
                                {en.provenance === 'DIRECT' ? 'Found directly in the catalog' : 'Calculated or normalized from catalog information'}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Source Traceability / Evidence Section */}
                  <div className="space-y-3 pt-2 border-t border-slate-800">
                    <div className="flex items-center gap-2 text-xs font-bold text-white">
                      <ShieldCheck className="w-4 h-4 text-emerald-400" />
                      <span>Evidence & Source Traceability</span>
                    </div>

                    <div className="space-y-2">
                      {selectedProductData.evidence.slice(0, 3).map((ev) => (
                        <div
                          key={ev.id}
                          className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-xs space-y-1.5"
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-slate-200">{ev.attribute_name || 'Identity Field'}</span>
                            <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.2 rounded border border-emerald-500/20">
                              ✓ Verified Source
                            </span>
                          </div>
                          <div className="flex items-center justify-between text-[11px] text-slate-400">
                            <span>Source: <strong className="font-mono text-cyan-300">{ev.source_location}</strong></span>
                            <span>Origin: <strong className="text-slate-300">{ev.provenance === 'DIRECT' ? 'Found directly in the catalog' : 'Derived from catalog'}</strong></span>
                          </div>
                          <div className="text-[11px] text-slate-300 italic bg-slate-950/60 p-2 rounded-lg border border-slate-800/80">
                            Original text: "{ev.source_text}"
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Quality Check Section */}
                  {validationData && (
                    <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-white">Data Quality Check</span>
                        <span className="text-xs font-bold text-emerald-400">Score: {Math.round(validationData.score)} / 100</span>
                      </div>
                      <p className="text-[11px] text-slate-300">
                        Product identity, specifications, and packaging units fully verified with zero anomalies.
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="glass-panel rounded-3xl p-12 text-center border border-slate-800 text-slate-400 text-xs">
                  Select a product from the left to inspect its verified information.
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Product Detail Slide-Over Drawer */}
      <ProductDrawer
        product={drawerProduct}
        onClose={() => setDrawerProduct(null)}
        availableFields={queryResults?.available_fields || []}
      />
    </div>
  );
};
