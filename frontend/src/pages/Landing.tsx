import React, { useState, useEffect } from 'react';
import {
  ArrowRight,
  Sparkles,
  ShieldCheck,
  Zap,
  Layers,
  FileSpreadsheet,
  CheckCircle2,
  Lock,
  Database,
  Cpu,
  SlidersHorizontal,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import { SpecraLogo } from '../components/ui/SpecraLogo';

export const Landing: React.FC = () => {
  const { setActiveTab } = useApp();
  const [activeStep, setActiveStep] = useState<number>(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveStep((prev) => (prev + 1) % 5);
    }, 2800);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="min-h-screen bg-[#07090e] text-slate-100 selection:bg-cyan-500 selection:text-slate-950 font-sans relative overflow-hidden">
      {/* Background Ambient Glows */}
      <div className="absolute top-[-150px] left-1/2 -translate-x-1/2 w-[900px] h-[500px] bg-gradient-to-b from-cyan-600/15 via-blue-600/10 to-transparent blur-[140px] pointer-events-none" />
      <div className="absolute top-[800px] -left-48 w-[600px] h-[600px] bg-blue-600/10 blur-[150px] pointer-events-none" />
      <div className="absolute top-[1400px] -right-48 w-[600px] h-[600px] bg-purple-600/10 blur-[150px] pointer-events-none" />

      {/* Top Navbar */}
      <header className="sticky top-0 z-40 w-full border-b border-white/5 bg-[#07090e]/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="cursor-pointer" onClick={() => setActiveTab('landing')}>
            <SpecraLogo size="md" />
          </div>

          <nav className="hidden md:flex items-center gap-8 text-xs font-semibold text-slate-400">
            <a href="#how-it-works" className="hover:text-white transition-colors">How it works</a>
            <a href="#industrial" className="hover:text-white transition-colors">Industrial Catalog</a>
            <a href="#why-specra" className="hover:text-white transition-colors">Why SPECra</a>
            <a href="#security" className="hover:text-white transition-colors">Security</a>
          </nav>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setActiveTab('login')}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-300 hover:text-white hover:bg-slate-800/80 transition-all"
            >
              Sign in
            </button>
            <button
              onClick={() => setActiveTab('upload')}
              className="px-5 py-2.5 rounded-xl text-xs font-bold bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition-all shadow-lg shadow-cyan-500/20 flex items-center gap-1.5"
            >
              <span>Start with your catalog</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </header>

      {/* HERO SECTION */}
      <section className="relative pt-16 pb-24 md:pt-24 md:pb-32 max-w-7xl mx-auto px-6">
        <div className="text-center space-y-6 max-w-4xl mx-auto">
          {/* Trust Badge */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-900/90 border border-slate-800 text-xs font-medium text-slate-300 shadow-inner">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
            <span>Built by Team DEADLOCK</span>
            <span className="text-slate-600">•</span>
            <span className="text-cyan-400 font-semibold">UniHack 2026</span>
          </div>

          {/* Main Hero Headline */}
          <h1 className="text-4xl sm:text-6xl md:text-7xl font-extrabold tracking-tight leading-[1.08] text-white">
            Turn messy product data into <span className="specra-accent-gradient-text">intelligence.</span>
          </h1>

          <p className="text-base sm:text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed font-normal">
            Transform fragmented industrial product catalogs into structured, enriched, validated and commerce-ready product intelligence.
          </p>

          {/* Action CTAs */}
          <div className="pt-4 flex flex-wrap items-center justify-center gap-4">
            <button
              onClick={() => setActiveTab('upload')}
              className="px-8 py-4 rounded-2xl text-sm font-bold bg-gradient-to-r from-cyan-500 via-blue-500 to-cyan-500 hover:from-cyan-400 hover:to-cyan-400 text-slate-950 transition-all shadow-xl shadow-cyan-500/25 flex items-center gap-2.5 transform hover:-translate-y-0.5 cursor-pointer"
            >
              <Zap className="w-4 h-4" />
              <span>Start with your catalog</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => setActiveTab('login')}
              className="px-6 py-4 rounded-2xl text-sm font-semibold bg-slate-900/80 hover:bg-slate-800 text-slate-200 border border-slate-700/80 transition-all flex items-center gap-2"
            >
              <span>Explore workspace</span>
            </button>
          </div>
        </div>

        {/* HERO INTERACTIVE TRANSFORMATION VISUAL */}
        <div className="mt-16 md:mt-20 max-w-5xl mx-auto">
          <div className="specra-panel rounded-3xl p-6 md:p-8 relative overflow-hidden border border-slate-700/50 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-6">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-rose-500/80" />
                <div className="w-3 h-3 rounded-full bg-amber-500/80" />
                <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
                <span className="text-xs font-mono text-slate-400 ml-2">SPECra Catalog Intelligence Engine</span>
              </div>
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Live Interactive Architecture
              </span>
            </div>

            {/* 5 Transformation Nodes Grid */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-3 relative">
              {/* Node 1: Raw Catalog */}
              <div
                onClick={() => setActiveStep(0)}
                className={`p-4 rounded-2xl border transition-all cursor-pointer ${
                  activeStep === 0
                    ? 'bg-slate-900 border-cyan-500 shadow-lg shadow-cyan-500/15 ring-1 ring-cyan-500/30'
                    : 'bg-slate-950/60 border-slate-800/80 opacity-70 hover:opacity-100'
                }`}
              >
                <div className="flex items-center justify-between">
                  <FileSpreadsheet className="w-5 h-5 text-cyan-400" />
                  <span className="text-[10px] font-mono text-slate-400">01 RAW</span>
                </div>
                <div className="text-xs font-bold text-white mt-3">Raw Catalog</div>
                <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">
                  Unstructured CSV with mixed units & messy part descriptions.
                </p>
              </div>

              {/* Node 2: AI Extraction */}
              <div
                onClick={() => setActiveStep(1)}
                className={`p-4 rounded-2xl border transition-all cursor-pointer ${
                  activeStep === 1
                    ? 'bg-slate-900 border-indigo-500 shadow-lg shadow-indigo-500/15 ring-1 ring-indigo-500/30'
                    : 'bg-slate-950/60 border-slate-800/80 opacity-70 hover:opacity-100'
                }`}
              >
                <div className="flex items-center justify-between">
                  <Cpu className="w-5 h-5 text-indigo-400" />
                  <span className="text-[10px] font-mono text-slate-400">02 AI</span>
                </div>
                <div className="text-xs font-bold text-white mt-3">AI Intelligence</div>
                <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">
                  Extracts specifications, dimensions, diameter, and grit.
                </p>
              </div>

              {/* Node 3: Enrichment */}
              <div
                onClick={() => setActiveStep(2)}
                className={`p-4 rounded-2xl border transition-all cursor-pointer ${
                  activeStep === 2
                    ? 'bg-slate-900 border-blue-500 shadow-lg shadow-blue-500/15 ring-1 ring-blue-500/30'
                    : 'bg-slate-950/60 border-slate-800/80 opacity-70 hover:opacity-100'
                }`}
              >
                <div className="flex items-center justify-between">
                  <Layers className="w-5 h-5 text-blue-400" />
                  <span className="text-[10px] font-mono text-slate-400">03 ENRICH</span>
                </div>
                <div className="text-xs font-bold text-white mt-3">Enrichment</div>
                <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">
                  Deterministic packaging normalization & unit parsing.
                </p>
              </div>

              {/* Node 4: Validation */}
              <div
                onClick={() => setActiveStep(3)}
                className={`p-4 rounded-2xl border transition-all cursor-pointer ${
                  activeStep === 3
                    ? 'bg-slate-900 border-amber-500 shadow-lg shadow-amber-500/15 ring-1 ring-amber-500/30'
                    : 'bg-slate-950/60 border-slate-800/80 opacity-70 hover:opacity-100'
                }`}
              >
                <div className="flex items-center justify-between">
                  <ShieldCheck className="w-5 h-5 text-amber-400" />
                  <span className="text-[10px] font-mono text-slate-400">04 VALIDATE</span>
                </div>
                <div className="text-xs font-bold text-white mt-3">Validation</div>
                <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">
                  Rule engine verification and score certification.
                </p>
              </div>

              {/* Node 5: Commerce-Ready */}
              <div
                onClick={() => setActiveStep(4)}
                className={`p-4 rounded-2xl border transition-all cursor-pointer ${
                  activeStep === 4
                    ? 'bg-slate-900 border-emerald-500 shadow-lg shadow-emerald-500/15 ring-1 ring-emerald-500/30'
                    : 'bg-slate-950/60 border-slate-800/80 opacity-70 hover:opacity-100'
                }`}
              >
                <div className="flex items-center justify-between">
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  <span className="text-[10px] font-mono text-slate-400">05 EXPORT</span>
                </div>
                <div className="text-xs font-bold text-white mt-3">Commerce-Ready</div>
                <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">
                  UniHack 252-column delivery dataset with evidence anchors.
                </p>
              </div>
            </div>

            {/* Active Node Detail Card Display */}
            <div className="mt-6 p-5 rounded-2xl bg-slate-950/90 border border-slate-800 animate-fadeIn">
              {activeStep === 0 && (
                <div className="space-y-2">
                  <span className="text-[10px] font-bold text-cyan-400 uppercase">Input Catalog Row</span>
                  <div className="font-mono text-xs text-slate-300 bg-slate-900 p-3 rounded-xl border border-slate-800/80">
                    3MABR-7100048736, "3M 775L Stikit Film P80 - Cubitron II 50 Disc/Box", Jam Industrial Supply LLC
                  </div>
                </div>
              )}
              {activeStep === 1 && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                  <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                    <span className="text-[10px] text-slate-400">Brand</span>
                    <div className="font-bold text-white">3M (100% confidence)</div>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                    <span className="text-[10px] text-slate-400">Diameter</span>
                    <div className="font-bold text-cyan-300">5 in (Extracted)</div>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                    <span className="text-[10px] text-slate-400">Abrasive Grit</span>
                    <div className="font-bold text-slate-200">80 (P80)</div>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                    <span className="text-[10px] text-slate-400">Backing Type</span>
                    <div className="font-bold text-slate-200">Film (Stikit)</div>
                  </div>
                </div>
              )}
              {activeStep === 2 && (
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
                  <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                    <span className="text-[10px] text-slate-400">Selling Qty</span>
                    <div className="font-bold text-white">50 [Normalized]</div>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                    <span className="text-[10px] text-slate-400">Selling UOM</span>
                    <div className="font-bold text-white">Box [Standardized]</div>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                    <span className="text-[10px] text-slate-400">Packaging Info</span>
                    <div className="font-bold text-indigo-300">50 pieces per Box</div>
                  </div>
                </div>
              )}
              {activeStep === 3 && (
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-400 font-bold flex items-center justify-center text-sm border border-emerald-500/20">
                      100
                    </div>
                    <div>
                      <div className="font-bold text-white">Quality Audit Passed</div>
                      <div className="text-[11px] text-slate-400">Zero unit conflicts • Identity verified • Exact source quote anchored</div>
                    </div>
                  </div>
                  <span className="px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 font-semibold text-[11px] border border-emerald-500/20">
                    Certified
                  </span>
                </div>
              )}
              {activeStep === 4 && (
                <div className="flex items-center justify-between text-xs">
                  <div className="space-y-1">
                    <span className="font-bold text-white">UniHack 252-Column Structured Delivery Dataset</span>
                    <div className="text-[11px] text-slate-400">Ready for instant ERP, distributor portals, and commerce feeds.</div>
                  </div>
                  <button
                    onClick={() => setActiveTab('upload')}
                    className="px-4 py-2 rounded-xl bg-cyan-500 text-slate-950 font-bold text-xs hover:bg-cyan-400 transition-all"
                  >
                    Try with your catalog →
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 1: FROM MESSY DATA TO INTELLIGENCE */}
      <section id="how-it-works" className="py-20 border-t border-slate-800/80 max-w-7xl mx-auto px-6">
        <div className="text-center space-y-3 mb-16">
          <span className="text-xs font-bold text-cyan-400 uppercase tracking-wider">End-To-End Transformation</span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white">
            From messy data to product intelligence.
          </h2>
          <p className="text-sm text-slate-400 max-w-xl mx-auto">
            A continuous, traceable pipeline purpose-built for the complexity of industrial trade.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="specra-card rounded-2xl p-6 space-y-3">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/10 text-cyan-400 flex items-center justify-center font-bold text-xs">
              01
            </div>
            <h3 className="text-sm font-bold text-white">Raw Catalog</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Upload CSV or Excel files with non-standard columns, missing codes, and combined specs.
            </p>
          </div>

          <div className="specra-card rounded-2xl p-6 space-y-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center font-bold text-xs">
              02
            </div>
            <h3 className="text-sm font-bold text-white">Understand</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              SPECra dynamically identifies product entities, brands, and technical descriptions without templates.
            </p>
          </div>

          <div className="specra-card rounded-2xl p-6 space-y-3">
            <div className="w-8 h-8 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center font-bold text-xs">
              03
            </div>
            <h3 className="text-sm font-bold text-white">Enrich</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Extract measurements, grit, packaging counts, and normalize units with deterministic rules.
            </p>
          </div>

          <div className="specra-card rounded-2xl p-6 space-y-3">
            <div className="w-8 h-8 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center font-bold text-xs">
              04
            </div>
            <h3 className="text-sm font-bold text-white">Validate</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Every field is checked for completeness, physical realism, and anchored to exact source text.
            </p>
          </div>

          <div className="specra-card rounded-2xl p-6 space-y-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center font-bold text-xs">
              05
            </div>
            <h3 className="text-sm font-bold text-white">Export</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Download clean CSV, Excel, or standard 252-column datasets ready for downstream commerce.
            </p>
          </div>
        </div>
      </section>

      {/* SECTION 2: BUILT FOR INDUSTRIAL CATALOGS */}
      <section id="industrial" className="py-20 border-t border-slate-800/80 max-w-7xl mx-auto px-6">
        <div className="text-center space-y-3 mb-16">
          <span className="text-xs font-bold text-cyan-400 uppercase tracking-wider">Domain Engineering</span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white">
            Built specifically for industrial catalogs.
          </h2>
          <p className="text-sm text-slate-400 max-w-xl mx-auto">
            Industrial SKUs carry intricate dimensions, tolerances, and packaging. SPECra standardizes them all.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="specra-panel rounded-3xl p-6 space-y-3 border border-slate-800">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center">
              <Database className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-white">Product Identity</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Resolves manufacturer part numbers (MPN), internal SKUs, UPCs, and brand taxonomies accurately.
            </p>
          </div>

          <div className="specra-panel rounded-3xl p-6 space-y-3 border border-slate-800">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center">
              <SlidersHorizontal className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-white">Technical Specifications</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Dissects complex abrasive grits, voltage ratings, material backings, and mechanical attributes.
            </p>
          </div>

          <div className="specra-panel rounded-3xl p-6 space-y-3 border border-slate-800">
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 text-blue-400 flex items-center justify-center">
              <Zap className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-white">Dimensions & Units</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Parses fractions (e.g. 1/2"x18"), millimeters, and inches into clean decimal values with explicit units.
            </p>
          </div>

          <div className="specra-panel rounded-3xl p-6 space-y-3 border border-slate-800">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
              <Layers className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-white">Packaging & UOM</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Calculates pack quantities, standard packaging strings, and unit-of-measure codes automatically.
            </p>
          </div>

          <div className="specra-panel rounded-3xl p-6 space-y-3 border border-slate-800">
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center">
              <Sparkles className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-white">Brand & Manufacturer</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Distinguishes parent manufacturers from distribution brands with deterministic cross-source checks.
            </p>
          </div>

          <div className="specra-panel rounded-3xl p-6 space-y-3 border border-slate-800">
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 text-purple-400 flex items-center justify-center">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-white">Evidence & Provenance</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Anchors every attribute to its exact source text in the raw catalog for absolute compliance and trust.
            </p>
          </div>
        </div>
      </section>

      {/* SECTION 3: WHY SPECRA */}
      <section id="why-specra" className="py-20 border-t border-slate-800/80 max-w-7xl mx-auto px-6">
        <div className="text-center space-y-3 mb-16">
          <span className="text-xs font-bold text-cyan-400 uppercase tracking-wider">Enterprise Trust</span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white">Why SPECra?</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="specra-panel rounded-3xl p-8 space-y-4 border border-slate-800">
            <div className="text-xs font-bold text-cyan-400 uppercase tracking-wider">Accurate</div>
            <h3 className="text-lg font-bold text-white">Extract only what your source supports.</h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              SPECra never hallucinates missing fields. If a specification is not in your catalog, it is marked as unavailable.
            </p>
          </div>

          <div className="specra-panel rounded-3xl p-8 space-y-4 border border-slate-800">
            <div className="text-xs font-bold text-indigo-400 uppercase tracking-wider">Traceable</div>
            <h3 className="text-lg font-bold text-white">Every attribute is traced to evidence.</h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              Inspect the exact raw column and substring quote behind every extracted number, measurement, and unit.
            </p>
          </div>

          <div className="specra-panel rounded-3xl p-8 space-y-4 border border-slate-800">
            <div className="text-xs font-bold text-emerald-400 uppercase tracking-wider">Scalable</div>
            <h3 className="text-lg font-bold text-white">Process large catalogs consistently.</h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              Combines lightweight Google Gemini 3.5 Flash Lite intelligence with lightning-fast deterministic PostgreSQL enrichment.
            </p>
          </div>
        </div>
      </section>

      {/* SECTION 4: SECURITY */}
      <section id="security" className="py-20 border-t border-slate-800/80 max-w-7xl mx-auto px-6">
        <div className="specra-panel rounded-3xl p-8 md:p-12 border border-slate-800 relative overflow-hidden bg-gradient-to-br from-slate-900/90 to-slate-950">
          <div className="max-w-2xl space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 text-xs font-semibold">
              <Lock className="w-3.5 h-3.5" />
              <span>Enterprise Data Architecture</span>
            </div>
            <h2 className="text-3xl font-bold text-white tracking-tight">Your catalog belongs to you.</h2>
            <p className="text-sm text-slate-300 leading-relaxed">
              SPECra operates with isolated workspaces, private processing jobs, and strict credential isolation.
              Your product catalog is processed in dedicated environments and never shared.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-4 text-xs text-slate-300">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Isolated Workspace Architecture</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Controlled Processing & Quota Management</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Deterministic Zero-Leakage Pipeline</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Local & Private Dataset Delivery</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FINAL CTA SECTION */}
      <section className="py-20 border-t border-slate-800 text-center max-w-4xl mx-auto px-6 space-y-6">
        <h2 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight">
          Ready to make your product data useful?
        </h2>
        <p className="text-sm text-slate-300 max-w-lg mx-auto">
          Start in seconds with your industrial CSV or Excel catalog. No complex configuration required.
        </p>
        <div className="pt-2">
          <button
            onClick={() => setActiveTab('upload')}
            className="px-8 py-4 rounded-2xl text-sm font-bold bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition-all shadow-xl shadow-cyan-500/25 inline-flex items-center gap-2 cursor-pointer"
          >
            <span>Start analyzing</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-slate-800/80 bg-slate-950/60 py-12">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-6">
          <SpecraLogo size="sm" showTagline />

          <div className="text-xs text-slate-400 font-medium text-center md:text-right">
            Built by <strong className="text-slate-200">DEADLOCK</strong> • UniHack 2026
          </div>
        </div>
      </footer>
    </div>
  );
};
