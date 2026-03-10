'use client';

import { Play, Activity, Mail, RefreshCw, Calendar, Users, Send } from 'lucide-react';
import { triggerPhase } from '@/lib/api';
import { useState } from 'react';

export default function ControlPanel() {
  const [loading, setLoading] = useState<string | null>(null);
  const [email, setEmail] = useState('');
  const [weeks, setWeeks] = useState(12);
  const [limit, setLimit] = useState(500);

  const handleAction = async (phase: 'scrape' | 'analyze' | 'pulsar' | 'email') => {
    setLoading(phase);
    try {
      await triggerPhase(phase, {
        email: phase === 'email' ? email : undefined,
        weeks: phase === 'scrape' ? weeks : undefined,
        limit: phase === 'scrape' ? limit : undefined,
      });
      alert(`Successfully triggered: ${phase.toUpperCase()}`);
    } catch (error) {
      alert(`Error triggering ${phase}: ${error}`);
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="space-y-6 mb-10">
      <div className="glass-card p-6 rounded-2xl flex flex-wrap items-center gap-8">
        <div className="flex items-center gap-4">
          <div className="p-2 bg-blue-500/10 rounded-lg">
            <Calendar className="text-blue-400" size={20} />
          </div>
          <div>
            <label className="block text-[10px] uppercase tracking-wider text-slate-400 font-bold mb-1">Time Range</label>
            <select 
              value={weeks} 
              onChange={(e) => setWeeks(Number(e.target.value))}
              className="bg-transparent text-sm font-semibold outline-none cursor-pointer"
            >
              <option value={8} className="bg-slate-800">Last 8 Weeks</option>
              <option value={12} className="bg-slate-800">Last 12 Weeks</option>
            </select>
          </div>
        </div>

        <div className="w-px h-10 bg-slate-700 hidden md:block"></div>

        <div className="flex items-center gap-4">
          <div className="p-2 bg-purple-500/10 rounded-lg">
            <Users className="text-purple-400" size={20} />
          </div>
          <div>
            <label className="block text-[10px] uppercase tracking-wider text-slate-400 font-bold mb-1">Review Limit</label>
            <select 
              value={limit} 
              onChange={(e) => setLimit(Number(e.target.value))}
              className="bg-transparent text-sm font-semibold outline-none cursor-pointer"
            >
              <option value={100} className="bg-slate-800">100 Reviews</option>
              <option value={250} className="bg-slate-800">250 Reviews</option>
              <option value={500} className="bg-slate-800">500 Reviews</option>
            </select>
          </div>
        </div>

        <button
          onClick={() => handleAction('scrape')}
          disabled={!!loading}
          className="ml-auto flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl transition-all font-semibold text-sm shadow-lg shadow-blue-500/20 disabled:opacity-50"
        >
          <RefreshCw className={loading === 'scrape' ? 'animate-spin' : ''} size={18} />
          Sync Data
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="glass-card p-4 rounded-2xl flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-500/10 rounded-lg">
              <Activity className="text-indigo-400" size={18} />
            </div>
            <span className="text-sm font-medium text-slate-200">Refine Categories</span>
          </div>
          <button
            onClick={() => handleAction('analyze')}
            disabled={!!loading}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-all text-xs font-bold disabled:opacity-50"
          >
            Run Llama Engine
          </button>
        </div>

        <div className="glass-card p-4 rounded-2xl flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-fuchsia-500/10 rounded-lg">
              <Play className="text-fuchsia-400" size={18} />
            </div>
            <span className="text-sm font-medium text-slate-200">Intelligence Report</span>
          </div>
          <button
            onClick={() => handleAction('pulsar')}
            disabled={!!loading}
            className="px-4 py-2 bg-fuchsia-600 hover:bg-fuchsia-500 text-white rounded-lg transition-all text-xs font-bold disabled:opacity-50"
          >
            Launch Gemini
          </button>
        </div>
      </div>

      <div className="glass-card p-4 rounded-2xl flex flex-col md:flex-row gap-4 items-center">
        <div className="flex items-center gap-3 flex-1 w-full">
          <div className="p-2 bg-orange-500/10 rounded-lg">
            <Mail className="text-orange-400" size={18} />
          </div>
          <input
            type="email"
            placeholder="Recipient email for current report..."
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="bg-transparent border-none outline-none text-sm w-full placeholder:text-slate-500"
          />
        </div>
        <button
          onClick={() => handleAction('email')}
          disabled={!!loading}
          className="w-full md:w-auto flex items-center justify-center gap-2 px-6 py-2 bg-orange-600 hover:bg-orange-500 text-white rounded-xl transition-all text-xs font-bold shadow-lg shadow-orange-500/10 disabled:opacity-50"
        >
          <Send size={16} />
          Deliver Pulse
        </button>
      </div>
    </div>
  );
}
