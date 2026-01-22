"use client";

import { useEffect, useState } from 'react';

type Result = {
  test_id: string;
  category: string;
  prompt: string;
  response: string;
  passed: boolean;
};

export default function Home() {
  const [results, setResults] = useState<Result[]>([]);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    fetch('/results.json')
      .then(res => res.json())
      .then(data => setResults(data));
  }, []);

  const categories = ['all', ...Array.from(new Set(results.map(r => r.category)))];
  const filteredResults = filter === 'all' ? results : results.filter(r => r.category === filter);

  const passRate = results.length ? (results.filter(r => r.passed).length / results.length) * 100 : 0;

  return (
    <main className="min-h-screen bg-gray-50 p-8 font-sans">
      <div className="max-w-6xl mx-auto">
        <header className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">🏆 FRAI Benchmark Leaderboard</h1>
          <p className="text-gray-600">The definitive open-source AI safety & compliance benchmark.</p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow text-center">
            <div className="text-gray-500 text-sm uppercase tracking-wide font-semibold">Overall Score</div>
            <div className="text-5xl font-bold text-blue-600 mt-2">{passRate.toFixed(1)}%</div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow text-center">
            <div className="text-gray-500 text-sm uppercase tracking-wide font-semibold">Total Tests</div>
            <div className="text-5xl font-bold text-gray-800 mt-2">{results.length}</div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow text-center">
            <div className="text-gray-500 text-sm uppercase tracking-wide font-semibold">Categories</div>
            <div className="text-5xl font-bold text-gray-800 mt-2">{categories.length - 1}</div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="p-4 border-b border-gray-200 flex gap-4 overflow-x-auto">
            {categories.map(cat => (
              <button
                key={cat}
                onClick={() => setFilter(cat)}
                className={`px-4 py-2 rounded-full text-sm font-medium capitalize whitespace-nowrap ${filter === cat
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
              >
                {cat}
              </button>
            ))}
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Test ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Prompt</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Response</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredResults.map((result, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${result.passed
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                        }`}>
                        {result.passed ? 'PASS' : 'FAIL'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 capitalize">{result.category}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-500">{result.test_id}</td>
                    <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate" title={result.prompt}>{result.prompt}</td>
                    <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate" title={result.response}>{result.response}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </main>
  );
}
