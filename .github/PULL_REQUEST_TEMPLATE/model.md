---
name: Submit a model to the FRAI leaderboard
about: Add or update a model under `models/<provider>/*.yaml`
title: "Add model: <provider>/<model-id>"
labels: [model-submission]
---

## Model

- **Model id:** `<provider>/<model-id>` (must match `id:` in the YAML)
- **Provider:** openai / anthropic / azure / openrouter / google / custom
- **Homepage / card:** <URL>
- **License:** <apache-2.0 | proprietary | open-weights | ...>

## Submission mode

Pick one:

- [ ] **Hosted run** — OpenRouter model. CI will run the benchmark automatically using a
  budget-capped OpenRouter key. I have set `provider: openrouter` and included
  `pricing.prompt` + `pricing.completion`.
- [ ] **Local run** — I have run `python3 scripts/run_benchmark.py` locally against
  my endpoint and committed `results/submissions/<model-id-slug>.json` in this PR.

## Checklist

- [ ] Added exactly one YAML under `models/<provider>/<slug>.yaml`.
- [ ] `python3 scripts/validate_models.py` passes locally.
- [ ] Filled in `submitted_by` with my GitHub handle and `submission_date` (today).
- [ ] (Hosted) Pricing reflects current OpenRouter list price.
- [ ] (Local) Results JSON has one row per `(test_id, model)` and includes `score`,
  `passed`, `category`, `latency_ms`.

## Notes / caveats

<!-- Anything graders should know: quotas, reasoning effort settings, system prompt, etc. -->
