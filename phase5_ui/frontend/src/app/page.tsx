'use client';

import { useState, useEffect } from 'react';
import { fetchReviews, fetchAnalysis } from '@/lib/api';
import ControlPanel from '@/components/ControlPanel';
import ThemeChart from '@/components/ThemeChart';
import ReviewTable from '@/components/ReviewTable';
import { Activity, Star, MessageSquare, ShieldCheck, Zap, TrendingUp, Sparkles } from 'lucide-react';

export default function Dashboard() {
  const [reviews, setReviews] = useState([]);
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [reviewsData, analysisData] = await Promise.all([
          fetchReviews(100),
          fetchAnalysis()
        ]);
        setReviews(reviewsData);
        setAnalysis(analysisData);
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0f172a] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="h-12 w-12 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin"></div>
          <p className="text-sm font-bold uppercase tracking-widest text-slate-500">Initializing Engine...</p>
        </div>
      </div>
    );
  }

  const avgRating = reviews.length > 0 
    ? (reviews.reduce((acc: number, r: any) => acc + r.score, 0) / reviews.length).toFixed(1)
    : '0';

  return (
    <div className="min-h-screen bg-[#0f172a] selection:bg-blue-500/30">
      {/* Dynamic Header */}
      <nav className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-gradient-to-br from-blue-500 to-indigo-600 p-2.5 rounded-xl shadow-lg shadow-blue-500/20">
              <TrendingUp className="text-white" size={24} />
            </div>
            <div>
              <h1 className="text-xl font-black gradient-text tracking-tight uppercase">INDmoney Pulse</h1>
              <p className="text-[10px] text-slate-500 font-bold uppercase tracking-[0.2em]">Institutional Sentiment Intelligence</p>
            </div>
          </div>
          <div className="flex gap-4">
            <div className="flex items-center gap-2 px-4 py-2 bg-slate-800 rounded-xl border border-slate-700">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="text-xs font-bold text-slate-300">SYSTEM ACTIVE</span>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-6 py-10">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-10">
          {[
            { label: 'Avg Satisfaction', val: avgRating + ' / 5.0', icon: Star, color: 'text-blue-400', bg: 'bg-blue-400/10' },
            { label: 'Intelligence Depth', val: reviews.length + ' Reviews', icon: MessageSquare, color: 'text-indigo-400', bg: 'bg-indigo-400/10' },
            { label: 'AI Resolution', val: 'Llama 3.1 & Gemini', icon: Sparkles, color: 'text-fuchsia-400', bg: 'bg-fuchsia-400/10' },
            { label: 'Data Integrity', val: 'De-identified', icon: ShieldCheck, color: 'text-emerald-400', bg: 'bg-emerald-400/10' }
          ].map((stat, i) => (
            <div key={i} className="glass-card p-6 rounded-2xl">
              <div className="flex items-center gap-4 mb-3">
                <div className={`p-2 rounded-lg ${stat.bg}`}>
                  <stat.icon className={stat.color} size={18} />
                </div>
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{stat.label}</span>
              </div>
              <p className="text-2xl font-black text-slate-100">{stat.val}</p>
            </div>
          ))}
        </div>

        {/* Action Center */}
        <ControlPanel />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-10">
          {/* Intelligence Cluster */}
          <div className="lg:col-span-1">
            {analysis && <ThemeChart data={analysis.categorized_reviews || {}} />}
          </div>

          {/* Strategic Insight */}
          <div className="lg:col-span-2">
            <div className="glass-card p-8 rounded-2xl h-full flex flex-col">
              <div className="flex items-center justify-between mb-8">
                <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                  <Zap size={16} className="text-fuchsia-400" />
                  Signal Extraction
                </h3>
                <span className="text-[10px] font-bold px-3 py-1 bg-fuchsia-500/10 text-fuchsia-400 rounded-full">LATEST ANALYSIS</span>
              </div>
              
              <div className="space-y-6 flex-1">
                {analysis?.top_quotes?.map((quote: string, i: number) => (
                  <div key={i} className="relative group">
                    <div className="absolute -left-4 top-0 bottom-0 w-1 bg-indigo-500/30 rounded-full group-hover:bg-indigo-500 transition-all"></div>
                    <blockquote className="text-slate-300 italic text-sm leading-relaxed pl-2 group-hover:text-white transition-colors">
                      "{quote}"
                    </blockquote>
                  </div>
                ))}
              </div>
              
              <div className="mt-10 pt-6 border-t border-slate-700/50 flex justify-between items-center bg-slate-800/20 -mx-8 -mb-8 p-8 rounded-b-2xl">
                <p className="text-[11px] text-slate-500 font-medium">Themes and quotes are dynamically extracted using Groq Llama 3.1 8B.</p>
                <div className="flex gap-2">
                   <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                   <div className="w-2 h-2 rounded-full bg-indigo-500"></div>
                   <div className="w-2 h-2 rounded-full bg-fuchsia-500"></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Global Feed */}
        <ReviewTable reviews={reviews} />

        {/* Footer */}
        <footer className="mt-20 text-center">
          <p className="text-[10px] text-slate-600 font-bold uppercase tracking-[0.3em]">Built for INDmoney • Strategic Review Intelligence v2.0</p>
        </footer>
      </div>
    </div>
  );
}
