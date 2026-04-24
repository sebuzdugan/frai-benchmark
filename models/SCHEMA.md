# Community Model Registry Schema

Every model evaluated by FRAI Benchmark lives in this directory as a single YAML file:

```
models/<provider>/<model-id>.yaml
```

`<provider>` is one of: `openai`, `anthropic`, `azure`, `openrouter`, `google`, `custom`.
`<model-id>` is a filesystem-safe slug of the model's canonical identifier
(`/` → `-`, lowercase).

Opening a PR that adds a file here is how you submit a new model to the leaderboard.
CI validates the schema, optionally runs the benchmark, and rebuilds the website.

## Required fields

| Field            | Type      | Description                                                                                      |
|------------------|-----------|--------------------------------------------------------------------------------------------------|
| `id`             | string    | Canonical model id as passed to the provider (e.g. `gpt-5.2`, `moonshotai/kimi-k2.6`).           |
| `display_name`   | string    | Human-readable label used on the leaderboard.                                                    |
| `provider`       | enum      | One of `openai` \| `anthropic` \| `azure` \| `openrouter` \| `google` \| `custom`.               |
| `route`          | enum      | One of `openrouter_chat` \| `azure_openai_chat` \| `azure_ai_inference` \| `azure_openai_responses` \| `openai_chat` \| `anthropic_messages` \| `custom_http`. |
| `submitted_by`   | string    | GitHub handle (include the `@`), e.g. `@sebuzdugan`.                                         |
| `submission_date`| string    | ISO date, e.g. `2026-04-24`.                                                                     |

## Optional fields

| Field       | Type            | Description                                                                       |
|-------------|-----------------|-----------------------------------------------------------------------------------|
| `pricing`   | object          | `{ prompt: <USD/token>, completion: <USD/token> }`. Required for `openrouter`.    |
| `params`    | object          | Per-model overrides, e.g. `{ max_tokens: 512, temperature: 0.2 }`.                |
| `tags`      | string[]        | Free-form labels displayed on the leaderboard (e.g. `open-weights`, `reasoning`). |
| `notes`     | string          | One-line description.                                                             |
| `homepage`  | string (URL)    | Link to the model's official page.                                                |
| `license`   | string          | License identifier (e.g. `apache-2.0`, `proprietary`, `open-weights`).            |
| `endpoint`  | string (URL)    | Override the default provider endpoint. Only used by `custom_http`.               |
| `env_keys`  | string[]        | Names of env vars required for this model. Documentation-only.                    |
| `premium`   | boolean         | If `true`, excluded from the default budget-capped CI run. Defaults to `false`.   |

## Example — hosted OpenRouter model (runs in CI)

```yaml
# models/openrouter/moonshotai-kimi-k2.6.yaml
id: moonshotai/kimi-k2.6
display_name: Kimi K2.6
provider: openrouter
route: openrouter_chat
pricing:
  prompt: 0.0000006
  completion: 0.0000028
tags: [open-weights, low-cost]
notes: Recent low-cost frontier open model.
homepage: https://openrouter.ai/moonshotai/kimi-k2.6
license: open-weights
submitted_by: "@sebuzdugan"
submission_date: "2026-04-24"
```

## Example — bring-your-own endpoint (local run)

```yaml
# models/custom/my-internal-llm.yaml
id: my-internal-llm
display_name: My Internal LLM
provider: custom
route: custom_http
endpoint: https://llm.example.com/v1/chat/completions
env_keys: [MY_INTERNAL_API_KEY]
params:
  max_tokens: 512
tags: [internal]
submitted_by: "@octocat"
submission_date: "2026-04-24"
```

For custom/internal models, run the benchmark locally and commit the resulting
`results/submissions/<model-id>.json` alongside the YAML in the same PR. See
[CONTRIBUTING.md](../CONTRIBUTING.md#submitting-a-model).
