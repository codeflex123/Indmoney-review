'use client';

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

interface ThemeChartProps {
  data: Record<string, number>;
}

export default function ThemeChart({ data }: ThemeChartProps) {
  const chartData = Object.entries(data).map(([name, value]) => ({ name, value }));
  const COLORS = ['#38bdf8', '#818cf8', '#fbbf24', '#f87171', '#4ade80', '#a78bfa'];

  return (
    <div className="glass-card p-6 rounded-2xl h-[400px]">
      <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-6">Discovery Clusters</h3>
      <div className="h-[calc(100%-40px)] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={70}
              outerRadius={100}
              paddingAngle={8}
              dataKey="value"
              stroke="none"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip 
              contentStyle={{ background: '#1e293b', border: 'none', borderRadius: '8px', color: '#fff' }}
              itemStyle={{ color: '#fff' }}
            />
            <Legend verticalAlign="bottom" wrapperStyle={{ paddingTop: '20px', fontSize: '12px' }} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
