"use client";

import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, LabelList } from 'recharts';
import { motion } from 'framer-motion';
import { Trophy, Shield, Activity, Zap, CheckCircle, AlertTriangle } from 'lucide-react';

type Result = {
  model: string;
  category: string;
  score: number;
  test_id: string;
  prompt: string;
  response: string;
};

type AggregatedResult = {
  model: string;
  avgScore: number;
  passRate: number;
  categories: { [key: string]: number };
};

const COLORS = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444'];

export default function Home() {
  const [data, setData] = useState<AggregatedResult[]>([]);
  const [rawData, setRawData] = useState<Result[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/results.json')
      .then(res => res.json())
      .then((json: Result[]) => {
        setRawData(json);

        // Aggregate Data
        const models = Array.from(new Set(json.map(r => r.model)));
        const aggregated = models.map(model => {
          const modelResults = json.filter(r => r.model === model);
          const avgScore = modelResults.reduce((acc, r) => acc + (r.score || 0), 0) / modelResults.length;
          const passedCount = modelResults.filter(r => (r.score || 0) >= 7).length;
          const passRate = (passedCount / modelResults.length) * 100;

          // Category Pass Scores
          const categories = Array.from(new Set(modelResults.map(r => r.category)));
          const catScores: { [key: string]: number } = {};
          categories.forEach(cat => {
            const catResults = modelResults.filter(r => r.category === cat);
            catScores[cat] = catResults.reduce((acc, r) => acc + (r.score || 0), 0) / catResults.length;
          });

          return { model, avgScore, passRate, categories: catScores };
        });

        // Sort by Score
        setData(aggregated.sort((a, b) => b.avgScore - a.avgScore));
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="min-h-screen bg-black text-white flex items-center justify-center">Loading Data...</div>;

  return (
    <main className="min-h-screen bg-[#0a0a0a] text-white p-8 font-sans selection:bg-purple-500 selection:text-white">
      <div className="max-w-5xl mx-auto space-y-12">

        {/* Header */}
        <header className="text-center space-y-4 pt-8">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-400 text-sm font-medium"
          >
            <Zap size={16} /> Live Benchmark Results v1.0
          </motion.div>
          <h1 className="text-6xl font-extrabold tracking-tight bg-gradient-to-r from-white via-gray-200 to-gray-500 bg-clip-text text-transparent">
            LLM Safety Leaderboard
          </h1>
          <p className="text-gray-400 max-w-2xl mx-auto text-lg">
            Evaluating SOTA models on bias, safety protocols, and regulatory compliance.
            <br />
            <span className="text-gray-600 text-sm">Powered by FRAI Engines</span>
          </p>
        </header>

        {/* Top Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {data.slice(0, 3).map((model, idx) => (
            <motion.div
              key={model.model}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1 }}
              className={`relative overflow-hidden p-6 rounded-2xl border ${idx === 0 ? 'border-yellow-500/50 bg-yellow-500/5 shadow-[0_0_40px_-10px_rgba(234,179,8,0.3)]' : 'border-gray-800 bg-gray-900/50'}`}
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <div className="text-gray-400 text-xs font-bold uppercase tracking-widest">{idx === 0 ? 'Champion' : `#${idx + 1} Ranked`}</div>
                  <h3 className="text-2xl font-bold mt-1 text-white">{model.model}</h3>
                </div>
                {idx === 0 && <Trophy className="text-yellow-500" size={24} />}
                {idx === 1 && <Shield className="text-gray-400" size={24} />}
                {idx === 2 && <Activity className="text-orange-400" size={24} />}
              </div>

              <div className="flex items-end gap-2">
                <span className="text-4xl font-mono font-bold">{model.avgScore.toFixed(2)}</span>
                <span className="text-sm text-gray-500 mb-1">/ 10.0</span>
              </div>

              <div className="mt-4 flex gap-2">
                <div className={`px-2 py-1 rounded text-xs font-bold ${model.passRate > 80 ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                  {model.passRate.toFixed(1)}% Pass Rate
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Main Chart */}
        <section className="bg-gray-900/30 border border-gray-800 rounded-3xl p-8 backdrop-blur-sm">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-2xl font-bold flex items-center gap-2">
              <Activity className="text-blue-500" /> Performance Comparison
            </h2>
            <div className="text-sm text-gray-500">Ranked by Average Safety Score</div>
          </div>

          <div className="h-[400px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data} layout="vertical" margin={{ left: 20, right: 20, top: 0, bottom: 0 }}>
                <XAxis type="number" domain={[0, 10]} hide />
                <YAxis dataKey="model" type="category" width={150} tick={{ fill: '#9ca3af', fontSize: 14 }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#111', border: '1px solid #333', borderRadius: '8px' }}
                  itemStyle={{ color: '#fff' }}
                />
                <Bar dataKey="avgScore" barSize={32} radius={[0, 4, 4, 0]}>
                  {data.map((entry, index) => {
                    const name = entry.model.toLowerCase();
                    let color = '#3b82f6'; // Default Blue

                    if (name.includes('gpt')) color = '#10b981';      // Emerald
                    else if (name.includes('deepseek')) color = '#8b5cf6'; // Violet
                    else if (name.includes('grok')) color = '#f59e0b';     // Amber
                    else if (name.includes('kimi')) color = '#ec4899';     // Pink
                    else if (name.includes('mistral')) color = '#f97316';  // Orange

                    return <Cell key={`cell-${index}`} fill={color} />;
                  })}
                  <LabelList
                    dataKey="avgScore"
                    position="insideRight"
                    formatter={(val: number) => `${((val / 10) * 100).toFixed(0)}%`}
                    style={{ fill: '#fff', fontSize: '13px', fontWeight: 'bold', textShadow: '0px 1px 2px rgba(0,0,0,0.5)' }}
                    offset={10}
                  />
                  {/* Label on top */}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* Detailed Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Render category heatmaps or specifics later */}
        </div>

        <footer className="text-center text-gray-600 text-sm py-8">
          Generated with FRAI Benchmark Engine • {new Date().toLocaleDateString()}
        </footer>

      </div>
    </main>
  );
}
