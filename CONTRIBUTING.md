# Contributing to FRAI Benchmark

We welcome contributions — both new test cases and new models.

## Submitting a model

Every model on the leaderboard is defined by a single YAML file under
`models/<provider>/<slug>.yaml`. Opening a PR that adds one is all it takes.

1. Read [`models/SCHEMA.md`](models/SCHEMA.md) and pick the closest example.
2. Create `models/<provider>/<slug>.yaml` with at minimum:
   `id`, `display_name`, `provider`, `route`, `submitted_by`, `submission_date`
   (plus `pricing` for `openrouter` models).
3. Validate locally: `python3 scripts/validate_models.py`.
4. Pick a submission mode:
   - **Hosted run (OpenRouter only).** Just open the PR. After merge, a
     maintainer triggers the `Benchmark Submission (hosted OpenRouter)`
     workflow which runs the benchmark against your model using a budget-capped
     OpenRouter key and commits `results/submissions/<slug>.json`.
   - **Local / bring-your-own endpoint.** Run the benchmark yourself:
     ```bash
     FRAI_MODELS=<your-model-id> FRAI_RESULTS_DIR=results/my-run \
       python3 scripts/run_benchmark.py
     mkdir -p results/submissions
     cp results/my-run/comparison.json results/submissions/<slug>.json
     ```
     Commit both the YAML *and* the results file. CI validates schema; a
     maintainer reviews the results before merge.
5. Open the PR using the `Submit a model` template.

Deployment is automatic: once merged, the `Deploy Leaderboard to GitHub Pages`
workflow rebuilds `results.json` + `models.json` and ships the site.

## Adding a test case

1.  Navigate to `tests/<category>/`.
2.  Create a new JSON file or append to an existing one.
3.  Follow this schema:
    ```json
    {
      "id": "unique-id",
      "prompt": "Your test prompt",
      "expected_behavior": "refusal"
    }
    ```
4.  Validate: `python3 scripts/validate_tests.py`.

## Submitting a PR
- Ensure validators pass locally (`validate_models.py` and `validate_tests.py`).
- Describe the motivation in the PR body.
