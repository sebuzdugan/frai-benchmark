"use client";

import { useEffect, useState } from 'react';
import { Activity, BarChart3, Gauge, ShieldCheck, Timer, Trophy, Zap } from 'lucide-react';

type Result = {
  model: string;
  category: string;
  score: number;
  test_id: string;
  prompt: string;
  response: string;
  passed?: boolean;
  latency_ms?: number;
};

type AggregatedResult = {
  model: string;
  avgScore: number;
  passRate: number;
  resultCount: number;
  avgLatency: number;
  categories: { [key: string]: number };
};

const CATEGORY_ORDER = ['bias', 'compliance', 'jailbreak', 'pii', 'safety'];
const MODEL_COLORS = ['#126b45', '#d79b21', '#256d85', '#a34b32', '#5b616e', '#7a5c96', '#2e7d32'];

function formatModelName(model: string) {
  return model
    .replace('google/', '')
    .replace('openrouter/', '')
    .replace('moonshotai/', '')
    .replace('arcee-ai/', '')
    .replace('x-ai/', '')
    .replace('z-ai/', '')
    .replace(':free', ' free');
}

function scoreClass(score: number) {
  if (score >= 8.5) return 'bg-[#0f6b43] text-white';
  if (score >= 7) return 'bg-[#b7d36b] text-[#1a210f]';
  if (score >= 5) return 'bg-[#f0bf58] text-[#261b05]';
  return 'bg-[#c84630] text-white';
}

export default function Home() {
  const [data, setData] = useState<AggregatedResult[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/results.json')
      .then(res => res.json())
      .then((json: Result[]) => {
        const models = Array.from(new Set(json.map(r => r.model)));
        const aggregated = models.map(model => {
          const modelResults = json.filter(r => r.model === model);
          const avgScore = modelResults.reduce((acc, r) => acc + (r.score || 0), 0) / modelResults.length;
          const passedCount = modelResults.filter(r => r.passed ?? (r.score || 0) >= 7).length;
          const passRate = (passedCount / modelResults.length) * 100;
          const avgLatency = modelResults.reduce((acc, r) => acc + (r.latency_ms || 0), 0) / modelResults.length;

          const catScores: { [key: string]: number } = {};
          CATEGORY_ORDER.forEach(cat => {
            const catResults = modelResults.filter(r => r.category === cat);
            catScores[cat] = catResults.length
              ? catResults.reduce((acc, r) => acc + (r.score || 0), 0) / catResults.length
              : 0;
          });

          return { model, avgScore, passRate, resultCount: modelResults.length, avgLatency, categories: catScores };
        });

        setData(aggregated.sort((a, b) => b.avgScore - a.avgScore));
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#f5f6f1] text-[#141712] flex items-center justify-center">
        <div className="flex items-center gap-3 text-sm font-semibold uppercase tracking-[0.18em]">
          <Activity className="animate-pulse text-[#126b45]" size={18} />
          Loading FRAI Results
        </div>
      </div>
    );
  }

  const leader = data[0];
  const totalResults = data.reduce((acc, model) => acc + model.resultCount, 0);
  const benchmarkAverage = data.reduce((acc, model) => acc + model.avgScore, 0) / data.length;
  const fastest = data.reduce((best, model) => model.avgLatency < best.avgLatency ? model : best, data[0]);

  return (
    <main className="min-h-screen bg-[#f4f6f1] text-[#141712] font-sans selection:bg-[#b7d36b] selection:text-[#141712]">
      <div className="mx-auto flex min-h-screen max-w-7xl flex-col px-6 py-5">
        <header className="flex items-center justify-between border-b border-[#d6dccf] pb-4">
          <div className="flex items-center gap-3">
            <div className="grid size-10 place-items-center rounded-lg bg-[#141712] text-white shadow-sm">
              <ShieldCheck size={21} />
            </div>
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#5c6659]">FRAI Benchmark</p>
              <p className="text-sm font-semibold text-[#141712]">OpenRouter Safety Run</p>
            </div>
          </div>
          <div className="hidden items-center gap-2 md:flex">
            {CATEGORY_ORDER.map(category => (
              <span key={category} className="rounded-lg border border-[#d6dccf] bg-white px-3 py-2 text-xs font-bold uppercase tracking-[0.13em] text-[#4f5a4c] shadow-sm">
                {category}
              </span>
            ))}
          </div>
        </header>

        <section className="grid flex-1 grid-cols-1 gap-6 py-6 lg:grid-cols-[1.02fr_1.35fr]">
          <div className="flex flex-col justify-between gap-6">
            <div className="space-y-6">
              <div className="inline-flex items-center gap-2 rounded-lg border border-[#c9d5bd] bg-white px-3 py-2 text-sm font-bold text-[#126b45] shadow-sm">
                <Zap size={16} />
                Budget-capped competitive run
              </div>
              <div>
                <h1 className="max-w-xl text-5xl font-black leading-[0.95] tracking-normal text-[#141712] md:text-6xl">
                  Safety leaderboard for modern LLMs.
                </h1>
                <p className="mt-5 max-w-lg text-lg leading-8 text-[#526050]">
                  A compact FRAI dashboard comparing refusal quality, PII handling, bias controls, compliance, and jailbreak resilience across current OpenRouter models.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-lg border border-[#d6dccf] bg-white p-4 shadow-sm">
                <div className="flex items-center justify-between text-[#5c6659]">
                  <span className="text-xs font-bold uppercase tracking-[0.15em]">Models</span>
                  <BarChart3 size={17} />
                </div>
                <div className="mt-4 text-4xl font-black">{data.length}</div>
              </div>
              <div className="rounded-lg border border-[#d6dccf] bg-white p-4 shadow-sm">
                <div className="flex items-center justify-between text-[#5c6659]">
                  <span className="text-xs font-bold uppercase tracking-[0.15em]">Results</span>
                  <Activity size={17} />
                </div>
                <div className="mt-4 text-4xl font-black">{totalResults}</div>
              </div>
              <div className="rounded-lg border border-[#d6dccf] bg-white p-4 shadow-sm">
                <div className="flex items-center justify-between text-[#5c6659]">
                  <span className="text-xs font-bold uppercase tracking-[0.15em]">Average</span>
                  <Gauge size={17} />
                </div>
                <div className="mt-4 text-4xl font-black">{benchmarkAverage.toFixed(1)}</div>
              </div>
              <div className="rounded-lg border border-[#d6dccf] bg-white p-4 shadow-sm">
                <div className="flex items-center justify-between text-[#5c6659]">
                  <span className="text-xs font-bold uppercase tracking-[0.15em]">Fastest</span>
                  <Timer size={17} />
                </div>
                <div className="mt-4 text-xl font-black leading-tight">{formatModelName(fastest.model)}</div>
              </div>
            </div>
          </div>

          <div className="grid gap-4">
            <section className="rounded-lg border border-[#1e271d] bg-[#141712] p-5 text-white shadow-xl">
              <div className="mb-5 flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs font-bold uppercase tracking-[0.18em] text-[#b7d36b]">Top performer</p>
                  <h2 className="mt-2 text-3xl font-black tracking-normal">{formatModelName(leader.model)}</h2>
                </div>
                <div className="grid size-12 place-items-center rounded-lg bg-[#d79b21] text-[#141712]">
                  <Trophy size={24} />
                </div>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div className="rounded-lg bg-white/8 p-4">
                  <p className="text-xs font-bold uppercase tracking-[0.16em] text-[#c8d2c3]">Score</p>
                  <p className="mt-3 text-4xl font-black">{leader.avgScore.toFixed(2)}</p>
                </div>
                <div className="rounded-lg bg-white/8 p-4">
                  <p className="text-xs font-bold uppercase tracking-[0.16em] text-[#c8d2c3]">Pass Rate</p>
                  <p className="mt-3 text-4xl font-black">{leader.passRate.toFixed(0)}%</p>
                </div>
                <div className="rounded-lg bg-white/8 p-4">
                  <p className="text-xs font-bold uppercase tracking-[0.16em] text-[#c8d2c3]">Rows</p>
                  <p className="mt-3 text-4xl font-black">{leader.resultCount}</p>
                </div>
              </div>
            </section>

            <section className="rounded-lg border border-[#d6dccf] bg-white p-5 shadow-sm">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="flex items-center gap-2 text-xl font-black">
                  <Activity className="text-[#126b45]" size={21} />
                  Model Scoreboard
                </h2>
                <span className="rounded-lg bg-[#eef2e7] px-3 py-2 text-xs font-bold uppercase tracking-[0.14em] text-[#526050]">
                  Score / 10
                </span>
              </div>

              <div className="grid gap-3">
                {data.map((entry, index) => (
                  <div key={entry.model} className="grid grid-cols-[178px_1fr_52px] items-center gap-3">
                    <div className="truncate text-sm font-black text-[#263024]" title={entry.model}>
                      {formatModelName(entry.model)}
                    </div>
                    <div className="h-9 overflow-hidden rounded-lg bg-[#eef2e7]">
                      <div
                        className="flex h-full items-center justify-end rounded-lg pr-3 text-sm font-black text-white shadow-sm"
                        style={{
                          width: `${Math.max(entry.avgScore * 10, 6)}%`,
                          backgroundColor: MODEL_COLORS[index % MODEL_COLORS.length],
                        }}
                      >
                        {entry.avgScore.toFixed(1)}
                      </div>
                    </div>
                    <div className="text-right text-sm font-black text-[#526050]">{entry.passRate.toFixed(0)}%</div>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </section>

        <section className="grid grid-cols-1 gap-3 border-t border-[#d6dccf] pt-5 md:grid-cols-7">
          {data.map(model => (
            <div key={model.model} className="rounded-lg border border-[#d6dccf] bg-white p-3 shadow-sm">
              <div className="mb-3 min-h-10 text-sm font-black leading-tight">{formatModelName(model.model)}</div>
              <div className="space-y-2">
                {CATEGORY_ORDER.map(category => (
                  <div key={category} className="flex items-center justify-between gap-2">
                    <span className="text-[11px] font-bold uppercase tracking-[0.12em] text-[#647060]">{category.slice(0, 4)}</span>
                    <span className={`min-w-10 rounded-md px-2 py-1 text-center text-xs font-black ${scoreClass(model.categories[category])}`}>
                      {model.categories[category] ? model.categories[category].toFixed(1) : '-'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </section>
      </div>
    </main>
  );
}
