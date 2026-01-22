# 🏆 FRAI Evaluation Benchmark (State of the Art)

> The definitive open-source AI safety & compliance benchmark.

## Goal
To become the go-to resource for evaluating LLMs on bias, safety, jailbreak resistance, and regulatory compliance, specifically targeting the **EU AI Act** and enterprise readiness.

## Key Features
*   **Rigorous Methodology**: Statistical significance (3 runs), version control, and confidence intervals.
*   **Comprehensive Test Suite**: 200+ questions across Bias, Safety, Jailbreak, PII, and Compliance.
*   **Multi-dimensional Scoring**: Granular scores (e.g., Bias -> Gender/Race/Age).
*   **Interactive Leaderboard**: Filter by category, compare models side-by-side, and track historical performance.

## Structure
*   `tests/`: JSON-based test suites.
*   `models/`: Model configurations and adapter definitions.
*   `results/`: Benchmark run outputs.
*   `website/`: Source code for the leaderboard.

## Quick Start
```bash
npm install
npm run benchmark -- --model=gpt-4o --test=all
```

## License
Apache 2.0
# frai-benchmark
