import React, { useState, useEffect } from 'react';
import {
  FileSpreadsheet,
  CheckCircle2,
  ArrowRight,
  Download,
  Search,
  FolderKanban,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import { listAllJobs } from '../api/ingestion';
import { downloadExportFile } from '../api/export';
import type { ProcessingJobResponse } from '../types/api';

export const MyData: React.FC = () => {
  const { setSelectedJobId, setActiveTab } = useApp();
  const [jobs, setJobs] = useState<ProcessingJobResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchFilter, setSearchFilter] = useState('');

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const data = await listAllJobs();
        setJobs(data);
      } catch (err) {
        console.error('Error fetching jobs:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchJobs();
  }, []);

  const filteredJobs = jobs.filter((j) =>
    j.filename.toLowerCase().includes(searchFilter.toLowerCase())
  );

  const handleOpenResults = (jobId: string) => {
    setSelectedJobId(jobId);
    setActiveTab('results');
  };

  const handleDownload = async (e: React.MouseEvent, jobId: string) => {
    e.stopPropagation();
    try {
      await downloadExportFile(jobId, 'xlsx');
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      {/* Header */}
      <div className="glass-panel rounded-3xl p-8 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">My Catalog Datasets</h2>
          <p className="text-xs text-slate-400 mt-1">
            Access previous catalog jobs, review extracted information, and download finished datasets.
          </p>
        </div>

        <button
          onClick={() => setActiveTab('upload')}
          className="px-5 py-2.5 rounded-xl text-xs font-bold bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition-all shadow-md shadow-cyan-500/20 flex items-center gap-2 self-start sm:self-auto"
        >
          <span>New Catalog Job</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Filter and Jobs Grid */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-slate-400">
            {filteredJobs.length} {filteredJobs.length === 1 ? 'Dataset' : 'Datasets'}
          </span>

          <div className="relative w-64">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search datasets..."
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              className="glass-input w-full pl-8 pr-3 py-1.5 rounded-lg text-xs"
            />
          </div>
        </div>

        {loading ? (
          <div className="p-12 text-center text-slate-400 text-xs">Loading datasets...</div>
        ) : filteredJobs.length === 0 ? (
          <div className="glass-panel rounded-2xl p-12 text-center border border-slate-800 space-y-3">
            <FolderKanban className="w-10 h-10 text-slate-500 mx-auto" />
            <h4 className="text-sm font-bold text-white">No datasets found</h4>
            <p className="text-xs text-slate-400">
              Upload your first catalog file to get started with DEADLOCK.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredJobs.map((job) => (
              <div
                key={job.id}
                onClick={() => handleOpenResults(job.id)}
                className="glass-card rounded-2xl p-6 border border-slate-800 hover:border-cyan-500/40 cursor-pointer transition-all hover:bg-slate-900/80 group space-y-4"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-11 h-11 rounded-xl bg-slate-800 flex items-center justify-center text-slate-300 group-hover:text-cyan-400 group-hover:bg-cyan-500/10 transition-colors">
                      <FileSpreadsheet className="w-6 h-6" />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-white truncate max-w-[200px]">
                        {job.filename}
                      </h4>
                      <p className="text-xs text-slate-400 mt-0.5">
                        Uploaded {new Date(job.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>

                  <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/20">
                    <CheckCircle2 className="w-3 h-3" />
                    Ready
                  </span>
                </div>

                <div className="pt-3 border-t border-slate-800 flex items-center justify-between text-xs">
                  <span className="text-slate-300 font-medium">
                    {job.total_records.toLocaleString()} Products
                  </span>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={(e) => handleDownload(e, job.id)}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                      title="Download Excel"
                    >
                      <Download className="w-3.5 h-3.5" />
                    </button>

                    <span className="text-cyan-400 font-semibold flex items-center gap-1 group-hover:translate-x-1 transition-transform">
                      <span>View Results</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
