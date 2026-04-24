"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  BarChart3,
  CheckCircle2,
  CheckSquare,
  Clock,
  Database,
  ExternalLink,
  Gauge,
  GitPullRequest,
  ShieldCheck,
  Square,
  Timer,
  Trophy,
  Users,
  Zap,
} from "lucide-react";

type ResultRow = {
  model: string;
  category: string;
  subcategory?: string;
  score: number | null;
  passed?: boolean | null;
  latency_ms?: number | null;
  test_id?: string;
};

type ModelMeta = {
  name: string;
  provider?: string;
  route?: string;
  display_name?: string;
  submitted_by?: string;
  submission_date?: string;
  homepage?: string;
  license?: string;
  tags?: string[];
  notes?: string;
  pricing?: { prompt?: number; completion?: number };
};

type AggregatedResult = {
  model: string;
  meta: ModelMeta | null;
  avgScore: number;
  passRate: number;
  resultCount: number;
  avgLatency: number;
  categories: Record<string, number>;
};

const CATEGORY_ORDER = ["bias", "compliance", "jailbreak", "pii", "safety"];
const MODEL_COLORS = [
  "#126b45",
  "#d79b21",
  "#256d85",
  "#a34b32",
  "#5b616e",
  "#7a5c96",
  "#2e7d32",
];
const BASE_PATH = process.env.NEXT_PUBLIC_BASE_PATH || "";
const REPO_URL =
  process.env.NEXT_PUBLIC_REPO_URL ||
  "https://github.com/sebuzdugan/frai-benchmark";

function asset(path: string) {
  return `${BASE_PATH}${path.startsWith("/") ? path : `/${path}`}`;
}

function formatModelName(meta: ModelMeta | null, fallback: string) {
  if (meta?.display_name) return meta.display_name;
  return fallback
    .replace("google/", "")
    .replace("openrouter/", "")
    .replace("moonshotai/", "")
    .replace("arcee-ai/", "")
    .replace("x-ai/", "")
    .replace("z-ai/", "")
    .replace(":free", " free");
}

function scoreClass(score: number) {
  if (score >= 8.5) return "bg-[#0f6b43] text-white";
  if (score >= 7) return "bg-[#b7d36b] text-[#1a210f]";
  if (score >= 5) return "bg-[#f0bf58] text-[#261b05]";
  return "bg-[#c84630] text-white";
}

function aggregate(
  rows: ResultRow[],
  models: Record<string, ModelMeta>,
  categoryFilter: string | null,
): AggregatedResult[] {
  const filtered = categoryFilter
    ? rows.filter((r) => r.category === categoryFilter)
    : rows;

  const grouped: Record<string, ResultRow[]> = {};
  for (const row of filtered) {
    if (!row.model) continue;
    (grouped[row.model] ||= []).push(row);
  }

  const entries = Object.entries(grouped).map(([model, modelRows]) => {
    const scores = modelRows.map((r) => r.score ?? 0);
    const avgScore = scores.reduce((a, b) => a + b, 0) / (scores.length || 1);
    const passed = modelRows.filter(
      (r) => r.passed ?? (r.score ?? 0) >= 7,
    ).length;
    const passRate = (passed / (modelRows.length || 1)) * 100;
    const avgLatency =
      modelRows.reduce((a, r) => a + (r.latency_ms ?? 0), 0) /
      (modelRows.length || 1);

    const categories: Record<string, number> = {};
    for (const cat of CATEGORY_ORDER) {
      const inCat = modelRows.filter((r) => r.category === cat);
      categories[cat] = inCat.length
        ? inCat.reduce((a, r) => a + (r.score ?? 0), 0) / inCat.length
        : 0;
    }

    return {
      model,
      meta: models[model] ?? null,
      avgScore,
      passRate,
      resultCount: modelRows.length,
      avgLatency,
      categories,
    };
  });

  return entries.sort((a, b) => b.avgScore - a.avgScore);
}

export default function Home() {
  const [rows, setRows] = useState<ResultRow[]>([]);
  const [models, setModels] = useState<Record<string, ModelMeta>>({});
  const [loading, setLoading] = useState(true);
  const [categoryFilter, setCategoryFilter] = useState<string | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [compareOpen, setCompareOpen] = useState(false);

  useEffect(() => {
    Promise.all([
      fetch(asset("/results.json")).then((r) => r.json()) as Promise<ResultRow[]>,
      fetch(asset("/models.json"))
        .then((r) => (r.ok ? r.json() : []))
        .catch(() => []) as Promise<ModelMeta[]>,
    ])
      .then(([resultRows, modelList]) => {
        setRows(resultRows);
        const map: Record<string, ModelMeta> = {};
        for (const m of modelList) map[m.name] = m;
        setModels(map);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const data = useMemo(
    () => aggregate(rows, models, categoryFilter),
    [rows, models, categoryFilter],
  );
  const registryList = useMemo(
    () =>
      Object.values(models).sort((a, b) =>
        (a.name ?? "").localeCompare(b.name ?? ""),
      ),
    [models],
  );
  const benchmarkedSet = useMemo(
    () => new Set(data.map((d) => d.model)),
    [data],
  );
  const registeredCount = registryList.length;
  const pendingCount = Math.max(registeredCount - data.length, 0);

  const toggleSelected = (model: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(model)) next.delete(model);
      else next.add(model);
      return next;
    });
  };

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

  if (!data.length && !registryList.length) {
    return (
      <div className="min-h-screen bg-[#f5f6f1] text-[#141712] flex items-center justify-center px-6">
        <div className="max-w-md text-center">
          <ShieldCheck className="mx-auto mb-4 text-[#126b45]" size={40} />
          <h1 className="text-2xl font-black">Leaderboard data missing</h1>
          <p className="mt-3 text-sm text-[#526050]">
            Run{" "}
            <code className="rounded bg-[#eef2e7] px-1">
              python scripts/build_leaderboard_data.py
            </code>{" "}
            in CI to populate{" "}
            <code className="rounded bg-[#eef2e7] px-1">results.json</code> and{" "}
            <code className="rounded bg-[#eef2e7] px-1">models.json</code>.
          </p>
        </div>
      </div>
    );
  }

  const hasResults = data.length > 0;
  const leader = hasResults ? data[0] : null;
  const totalResults = data.reduce((a, m) => a + m.resultCount, 0);
  const benchmarkAverage =
    data.reduce((a, m) => a + m.avgScore, 0) / (data.length || 1);
  const fastest = hasResults
    ? data.reduce(
        (best, m) => (m.avgLatency < best.avgLatency ? m : best),
        data[0],
      )
    : null;
  const selectedData = data.filter((d) => selected.has(d.model));

  const submitUrl = `${REPO_URL}/compare/main...main?quick_pull=1&template=model.md&labels=model-submission&title=${encodeURIComponent(
    "Add model: <provider>/<model-id>",
  )}`;

  return (
    <main className="min-h-screen bg-[#f4f6f1] text-[#141712] font-sans selection:bg-[#b7d36b] selection:text-[#141712]">
      <div className="mx-auto flex min-h-screen max-w-7xl flex-col px-6 py-5">
        <header className="flex flex-wrap items-center justify-between gap-4 border-b border-[#d6dccf] pb-4">
          <div className="flex items-center gap-3">
            <div className="grid size-10 place-items-center rounded-lg bg-[#141712] text-white shadow-sm">
              <ShieldCheck size={21} />
            </div>
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#5c6659]">
                FRAI Benchmark
              </p>
              <p className="text-sm font-semibold text-[#141712]">
                Community leaderboard · safety, bias, PII, jailbreak, compliance
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <a
              href={submitUrl}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 rounded-lg bg-[#141712] px-3 py-2 text-xs font-bold uppercase tracking-[0.14em] text-white shadow-sm hover:bg-[#2a2e28]"
            >
              <GitPullRequest size={14} />
              Submit your model
            </a>
            <a
              href={REPO_URL}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 rounded-lg border border-[#d6dccf] bg-white px-3 py-2 text-xs font-bold uppercase tracking-[0.14em] text-[#4f5a4c] shadow-sm hover:bg-[#eef2e7]"
            >
              <ExternalLink size={14} />
              Repo
            </a>
          </div>
        </header>

        <div className="mt-4 flex flex-wrap items-center gap-2">
          <span className="text-[11px] font-bold uppercase tracking-[0.16em] text-[#5c6659]">
            Filter
          </span>
          <button
            onClick={() => setCategoryFilter(null)}
            className={`rounded-lg border px-3 py-1.5 text-xs font-bold uppercase tracking-[0.13em] shadow-sm transition ${
              categoryFilter === null
                ? "border-[#141712] bg-[#141712] text-white"
                : "border-[#d6dccf] bg-white text-[#4f5a4c] hover:bg-[#eef2e7]"
            }`}
          >
            All
          </button>
          {CATEGORY_ORDER.map((category) => (
            <button
              key={category}
              onClick={() =>
                setCategoryFilter(category === categoryFilter ? null : category)
              }
              className={`rounded-lg border px-3 py-1.5 text-xs font-bold uppercase tracking-[0.13em] shadow-sm transition ${
                category === categoryFilter
                  ? "border-[#126b45] bg-[#126b45] text-white"
                  : "border-[#d6dccf] bg-white text-[#4f5a4c] hover:bg-[#eef2e7]"
              }`}
            >
              {category}
            </button>
          ))}
          <div className="ml-auto flex items-center gap-2">
            <span className="text-[11px] font-bold uppercase tracking-[0.14em] text-[#5c6659]">
              {selected.size} selected
            </span>
            <button
              disabled={selected.size < 2}
              onClick={() => setCompareOpen((v) => !v)}
              className="rounded-lg border border-[#d6dccf] bg-white px-3 py-1.5 text-xs font-bold uppercase tracking-[0.13em] shadow-sm transition disabled:opacity-40 enabled:hover:bg-[#eef2e7]"
            >
              {compareOpen ? "Hide compare" : "Compare"}
            </button>
            {selected.size > 0 && (
              <button
                onClick={() => {
                  setSelected(new Set());
                  setCompareOpen(false);
                }}
                className="text-xs font-bold uppercase tracking-[0.13em] text-[#5c6659] hover:text-[#141712]"
              >
                Clear
              </button>
            )}
          </div>
        </div>

        <section className="grid flex-1 grid-cols-1 gap-6 py-6 lg:grid-cols-[1.02fr_1.35fr]">
          <div className="flex flex-col justify-between gap-6">
            <div className="space-y-6">
              <div className="inline-flex items-center gap-2 rounded-lg border border-[#c9d5bd] bg-white px-3 py-2 text-sm font-bold text-[#126b45] shadow-sm">
                <Zap size={16} />
                Community-contributed runs
              </div>
              <div>
                <h1 className="max-w-xl text-5xl font-black leading-[0.95] tracking-normal text-[#141712] md:text-6xl">
                  Safety leaderboard for modern LLMs.
                </h1>
                <p className="mt-5 max-w-lg text-lg leading-8 text-[#526050]">
                  Evaluates refusal quality, PII handling, bias controls, EU AI
                  Act compliance, and jailbreak resilience. Add a model via PR
                  and CI runs it against the same 280-prompt test pool.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <StatCard label="Registered" icon={<Database size={17} />}>
                <div className="mt-4 text-4xl font-black">{registeredCount}</div>
                <div className="mt-1 text-[11px] font-bold uppercase tracking-[0.12em] text-[#647060]">
                  models
                </div>
              </StatCard>
              <StatCard label="Benchmarked" icon={<BarChart3 size={17} />}>
                <div className="mt-4 text-4xl font-black">{data.length}</div>
                <div className="mt-1 text-[11px] font-bold uppercase tracking-[0.12em] text-[#647060]">
                  {pendingCount} pending
                </div>
              </StatCard>
              <StatCard label="Test rows" icon={<Activity size={17} />}>
                <div className="mt-4 text-4xl font-black">{totalResults}</div>
              </StatCard>
              <StatCard label="Average" icon={<Gauge size={17} />}>
                <div className="mt-4 text-4xl font-black">
                  {hasResults ? benchmarkAverage.toFixed(1) : "—"}
                </div>
              </StatCard>
              <StatCard label="Fastest" icon={<Timer size={17} />}>
                <div className="mt-4 text-xl font-black leading-tight">
                  {fastest
                    ? formatModelName(fastest.meta, fastest.model)
                    : "—"}
                </div>
              </StatCard>
            </div>
          </div>

          <div className="grid gap-4">
            {leader ? (
              <section className="rounded-lg border border-[#1e271d] bg-[#141712] p-5 text-white shadow-xl">
                <div className="mb-5 flex items-start justify-between gap-4">
                  <div>
                    <p className="text-xs font-bold uppercase tracking-[0.18em] text-[#b7d36b]">
                      Top performer
                      {categoryFilter ? ` — ${categoryFilter}` : ""}
                    </p>
                    <h2 className="mt-2 text-3xl font-black tracking-normal">
                      {formatModelName(leader.meta, leader.model)}
                    </h2>
                    {leader.meta?.submitted_by && (
                      <p className="mt-2 inline-flex items-center gap-1.5 text-xs font-semibold text-[#b7d36b]">
                        <Users size={12} />
                        {leader.meta.submitted_by}
                      </p>
                    )}
                  </div>
                  <div className="grid size-12 place-items-center rounded-lg bg-[#d79b21] text-[#141712]">
                    <Trophy size={24} />
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <NightStat label="Score" value={leader.avgScore.toFixed(2)} />
                  <NightStat
                    label="Pass Rate"
                    value={`${leader.passRate.toFixed(0)}%`}
                  />
                  <NightStat
                    label="Rows"
                    value={leader.resultCount.toString()}
                  />
                </div>
              </section>
            ) : (
              <section className="rounded-lg border border-[#d79b21] bg-[#fffaec] p-5 shadow-sm">
                <p className="text-xs font-bold uppercase tracking-[0.18em] text-[#a15c0a]">
                  Benchmarks pending
                </p>
                <h2 className="mt-2 text-2xl font-black tracking-normal text-[#141712]">
                  {registeredCount} models registered, awaiting their next run.
                </h2>
                <p className="mt-2 text-sm text-[#4f5a4c]">
                  The community registry is populated below. Run{" "}
                  <code className="rounded bg-white px-1 py-0.5 text-xs">
                    python scripts/run_benchmark.py
                  </code>{" "}
                  or trigger the <strong>Benchmark Submission</strong>{" "}
                  workflow to fill the scoreboard.
                </p>
              </section>
            )}

            <section className="rounded-lg border border-[#d6dccf] bg-white p-5 shadow-sm">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="flex items-center gap-2 text-xl font-black">
                  <Activity className="text-[#126b45]" size={21} />
                  Model Scoreboard
                </h2>
                <span className="rounded-lg bg-[#eef2e7] px-3 py-2 text-xs font-bold uppercase tracking-[0.14em] text-[#526050]">
                  {categoryFilter ? `${categoryFilter} / 10` : "Score / 10"}
                </span>
              </div>

              <div className="grid gap-2">
                {data.map((entry, index) => {
                  const checked = selected.has(entry.model);
                  return (
                    <button
                      key={entry.model}
                      onClick={() => toggleSelected(entry.model)}
                      className={`grid grid-cols-[18px_180px_1fr_52px] items-center gap-3 rounded-md px-2 py-1.5 text-left transition ${
                        checked
                          ? "bg-[#eef2e7] ring-1 ring-[#126b45]"
                          : "hover:bg-[#f5f6f1]"
                      }`}
                    >
                      {checked ? (
                        <CheckSquare size={16} className="text-[#126b45]" />
                      ) : (
                        <Square size={16} className="text-[#b9c2b5]" />
                      )}
                      <div
                        className="truncate text-sm font-black text-[#263024]"
                        title={entry.model}
                      >
                        {formatModelName(entry.meta, entry.model)}
                        {entry.meta?.provider && (
                          <span className="ml-2 rounded bg-[#eef2e7] px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-[0.1em] text-[#526050]">
                            {entry.meta.provider}
                          </span>
                        )}
                      </div>
                      <div className="h-9 overflow-hidden rounded-lg bg-[#eef2e7]">
                        <div
                          className="flex h-full items-center justify-end rounded-lg pr-3 text-sm font-black text-white shadow-sm"
                          style={{
                            width: `${Math.max(entry.avgScore * 10, 6)}%`,
                            backgroundColor:
                              MODEL_COLORS[index % MODEL_COLORS.length],
                          }}
                        >
                          {entry.avgScore.toFixed(1)}
                        </div>
                      </div>
                      <div className="text-right text-sm font-black text-[#526050]">
                        {entry.passRate.toFixed(0)}%
                      </div>
                    </button>
                  );
                })}
              </div>
            </section>
          </div>
        </section>

        {compareOpen && selectedData.length >= 2 && (
          <section className="mb-6 rounded-lg border border-[#141712] bg-white p-5 shadow-sm">
            <h2 className="mb-4 flex items-center gap-2 text-lg font-black">
              <BarChart3 className="text-[#126b45]" size={19} />
              Side-by-side · {selectedData.length} models
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[#d6dccf] text-left text-[11px] font-bold uppercase tracking-[0.12em] text-[#647060]">
                    <th className="py-2 pr-4">Model</th>
                    <th className="py-2 pr-4">Provider</th>
                    <th className="py-2 pr-4">Avg</th>
                    <th className="py-2 pr-4">Pass %</th>
                    <th className="py-2 pr-4">Latency</th>
                    {CATEGORY_ORDER.map((cat) => (
                      <th key={cat} className="py-2 pr-4">
                        {cat}
                      </th>
                    ))}
                    <th className="py-2 pr-4">Contributor</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedData.map((entry) => (
                    <tr
                      key={entry.model}
                      className="border-b border-[#eef2e7] last:border-0"
                    >
                      <td className="py-2 pr-4 font-black text-[#263024]">
                        {formatModelName(entry.meta, entry.model)}
                      </td>
                      <td className="py-2 pr-4 text-[#526050]">
                        {entry.meta?.provider ?? "—"}
                      </td>
                      <td className="py-2 pr-4 font-bold">
                        {entry.avgScore.toFixed(2)}
                      </td>
                      <td className="py-2 pr-4">
                        {entry.passRate.toFixed(0)}%
                      </td>
                      <td className="py-2 pr-4 text-[#526050]">
                        {entry.avgLatency.toFixed(0)}ms
                      </td>
                      {CATEGORY_ORDER.map((cat) => (
                        <td key={cat} className="py-2 pr-4">
                          <span
                            className={`rounded px-2 py-0.5 text-xs font-black ${scoreClass(entry.categories[cat] ?? 0)}`}
                          >
                            {entry.categories[cat]
                              ? entry.categories[cat].toFixed(1)
                              : "-"}
                          </span>
                        </td>
                      ))}
                      <td className="py-2 pr-4 text-[#526050]">
                        {entry.meta?.submitted_by ?? "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {hasResults && (
          <section className="grid grid-cols-1 gap-3 border-t border-[#d6dccf] pt-5 md:grid-cols-4 lg:grid-cols-7">
            {data.map((model) => (
              <div
                key={model.model}
                className="rounded-lg border border-[#d6dccf] bg-white p-3 shadow-sm"
              >
                <div className="mb-1 min-h-10 text-sm font-black leading-tight">
                  {formatModelName(model.meta, model.model)}
                </div>
                {model.meta?.provider && (
                  <div className="mb-2 text-[9px] font-bold uppercase tracking-[0.1em] text-[#647060]">
                    {model.meta.provider}
                    {model.meta.submitted_by
                      ? ` · ${model.meta.submitted_by}`
                      : ""}
                  </div>
                )}
                <div className="space-y-2">
                  {CATEGORY_ORDER.map((category) => (
                    <div
                      key={category}
                      className="flex items-center justify-between gap-2"
                    >
                      <span className="text-[11px] font-bold uppercase tracking-[0.12em] text-[#647060]">
                        {category.slice(0, 4)}
                      </span>
                      <span
                        className={`min-w-10 rounded-md px-2 py-1 text-center text-xs font-black ${scoreClass(model.categories[category])}`}
                      >
                        {model.categories[category]
                          ? model.categories[category].toFixed(1)
                          : "-"}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </section>
        )}

        {registryList.length > 0 && (
          <section className="mt-6 rounded-lg border border-[#d6dccf] bg-white p-5 shadow-sm">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <h2 className="flex items-center gap-2 text-xl font-black">
                <Database className="text-[#126b45]" size={20} />
                Model Registry · {registeredCount} models
              </h2>
              <div className="flex items-center gap-3 text-[11px] font-bold uppercase tracking-[0.14em]">
                <span className="inline-flex items-center gap-1 rounded-md bg-[#eef2e7] px-2 py-1 text-[#126b45]">
                  <CheckCircle2 size={11} /> {data.length} benchmarked
                </span>
                <span className="inline-flex items-center gap-1 rounded-md bg-[#fffaec] px-2 py-1 text-[#a15c0a]">
                  <Clock size={11} /> {pendingCount} pending
                </span>
              </div>
            </div>
            <p className="mb-4 max-w-3xl text-[12px] text-[#526050]">
              Every model is defined by a YAML under{" "}
              <code className="rounded bg-[#eef2e7] px-1 text-[11px]">
                models/&lt;provider&gt;/
              </code>
              . Contributors open a PR, CI validates the schema, and the
              benchmark runs on merge. Pending rows show models awaiting their
              next scheduled run.
            </p>
            <div className="grid gap-2 md:grid-cols-2 lg:grid-cols-3">
              {registryList.map((m) => {
                const done = benchmarkedSet.has(m.name);
                return (
                  <div
                    key={m.name}
                    className={`rounded-lg border bg-white p-3 shadow-sm ${
                      done ? "border-[#c9d5bd]" : "border-[#d6dccf]"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0 flex-1">
                        <div className="truncate text-sm font-black text-[#263024]" title={m.name}>
                          {formatModelName(m, m.name)}
                        </div>
                        <div className="mt-0.5 truncate font-mono text-[10px] text-[#647060]">
                          {m.name}
                        </div>
                      </div>
                      <span
                        className={`inline-flex shrink-0 items-center gap-1 rounded-md px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-[0.12em] ${
                          done
                            ? "bg-[#eef2e7] text-[#126b45]"
                            : "bg-[#fffaec] text-[#a15c0a]"
                        }`}
                      >
                        {done ? <CheckCircle2 size={10} /> : <Clock size={10} />}
                        {done ? "scored" : "pending"}
                      </span>
                    </div>
                    <div className="mt-2 flex flex-wrap items-center gap-1 text-[9px] font-bold uppercase tracking-[0.1em]">
                      {m.provider && (
                        <span className="rounded bg-[#141712] px-1.5 py-0.5 text-white">
                          {m.provider}
                        </span>
                      )}
                      {m.license && (
                        <span className="rounded border border-[#d6dccf] bg-white px-1.5 py-0.5 text-[#4f5a4c]">
                          {m.license}
                        </span>
                      )}
                      {m.tags?.slice(0, 2).map((tag) => (
                        <span
                          key={tag}
                          className="rounded bg-[#eef2e7] px-1.5 py-0.5 text-[#526050]"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                    {m.submitted_by && (
                      <div className="mt-2 flex items-center gap-1 text-[10px] text-[#647060]">
                        <Users size={9} /> {m.submitted_by}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </section>
        )}

        <footer className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-[#d6dccf] pt-4 text-xs text-[#5c6659]">
          <span>
            Open-source · Apache 2.0 · Add your model with one YAML →{" "}
            <a
              className="font-bold underline"
              href={`${REPO_URL}/blob/main/models/SCHEMA.md`}
              target="_blank"
              rel="noreferrer"
            >
              models/SCHEMA.md
            </a>
          </span>
          <span>
            Methodology:{" "}
            <a
              className="font-bold underline"
              href={`${REPO_URL}/blob/main/METHODOLOGY.md`}
              target="_blank"
              rel="noreferrer"
            >
              panel-of-experts judging
            </a>
          </span>
        </footer>
      </div>
    </main>
  );
}

function StatCard({
  label,
  icon,
  children,
}: {
  label: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border border-[#d6dccf] bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between text-[#5c6659]">
        <span className="text-xs font-bold uppercase tracking-[0.15em]">
          {label}
        </span>
        {icon}
      </div>
      {children}
    </div>
  );
}

function NightStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-white/8 p-4">
      <p className="text-xs font-bold uppercase tracking-[0.16em] text-[#c8d2c3]">
        {label}
      </p>
      <p className="mt-3 text-4xl font-black">{value}</p>
    </div>
  );
}
