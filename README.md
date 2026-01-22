# FRAI Evaluation Benchmark

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
*   `scripts/`: Python benchmark runner and validation tools.
*   `results/`: Benchmark run outputs.
*   `website/`: Next.js leaderboard application.

## Quick Start
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Validate test cases
python scripts/validate_tests.py

# 3. Run benchmark
python scripts/run_benchmark.py
```

## License
Apache 2.0
