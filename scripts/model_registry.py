"""Shared Azure model registry for benchmark scripts."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Iterable, List, Optional

AZURE_OPENAI_CHAT = "azure_openai_chat"
AZURE_AI_INFERENCE = "azure_ai_inference"
AZURE_OPENAI_RESPONSES = "azure_openai_responses"
OPENROUTER_CHAT = "openrouter_chat"
UNSUPPORTED = "unsupported"

MODEL_ORDER = [
    "moonshotai/kimi-k2.6",
    "openrouter/elephant-alpha",
    "z-ai/glm-5.1",
    "google/gemma-4-31b-it:free",
    "qwen/qwen3.6-plus",
    "arcee-ai/trinity-large-thinking",
    "x-ai/grok-4.20",
    "gpt-5.4-pro",
    "gpt-5.2",
    "gpt-5.2-chat",
    "gpt-5.2-codex",
    "gpt-5.1",
    "gpt-4o",
    "DeepSeek-V3.2",
    "grok-4-fast-reasoning",
    "Kimi-K2-Thinking",
    "Mistral-Large-3",
]

DEFAULT_MODELS = [
    {"name": "gpt-5.4-pro", "route": AZURE_OPENAI_RESPONSES},
    {"name": "gpt-5.2", "route": AZURE_OPENAI_CHAT},
    {"name": "gpt-5.2-chat", "route": AZURE_OPENAI_CHAT},
    {"name": "gpt-5.2-codex", "route": AZURE_OPENAI_RESPONSES},
    {"name": "gpt-5.1", "route": AZURE_OPENAI_CHAT},
    {"name": "gpt-4o", "route": AZURE_OPENAI_CHAT},
    {"name": "DeepSeek-V3.2", "route": AZURE_OPENAI_CHAT},
    {"name": "grok-4-fast-reasoning", "route": AZURE_OPENAI_CHAT},
    {"name": "Kimi-K2-Thinking", "route": AZURE_OPENAI_CHAT},
    {"name": "Mistral-Large-3", "route": AZURE_AI_INFERENCE},
]

OPENROUTER_RECOMMENDED_MODELS = [
    {
        "name": "moonshotai/kimi-k2.6",
        "route": OPENROUTER_CHAT,
        "pricing": {"prompt": 0.0000006, "completion": 0.0000028},
        "notes": "Recent low-cost frontier open model.",
    },
    {
        "name": "openrouter/elephant-alpha",
        "route": OPENROUTER_CHAT,
        "pricing": {"prompt": 0.0, "completion": 0.0},
        "notes": "Free OpenRouter model.",
    },
    {
        "name": "z-ai/glm-5.1",
        "route": OPENROUTER_CHAT,
        "pricing": {"prompt": 0.000000698, "completion": 0.0000044},
        "notes": "Recent agentic/coding model.",
    },
    {
        "name": "google/gemma-4-31b-it:free",
        "route": OPENROUTER_CHAT,
        "pricing": {"prompt": 0.0, "completion": 0.0},
        "notes": "Free recent Gemma model.",
    },
    {
        "name": "qwen/qwen3.6-plus",
        "route": OPENROUTER_CHAT,
        "pricing": {"prompt": 0.000000325, "completion": 0.00000195},
        "notes": "Recent low-cost Qwen model.",
    },
    {
        "name": "arcee-ai/trinity-large-thinking",
        "route": OPENROUTER_CHAT,
        "pricing": {"prompt": 0.00000022, "completion": 0.00000085},
        "notes": "Low-cost reasoning model.",
    },
    {
        "name": "x-ai/grok-4.20",
        "route": OPENROUTER_CHAT,
        "pricing": {"prompt": 0.000002, "completion": 0.000006},
        "notes": "Competitive but more expensive than the other default picks.",
    },
]

OPENROUTER_PREMIUM_MODELS = [
    {
        "name": "anthropic/claude-opus-4.7",
        "route": OPENROUTER_CHAT,
        "pricing": {"prompt": 0.000005, "completion": 0.000025},
        "notes": "Premium model; not included by default for the $2 budget.",
    },
]


def registry_path() -> str:
    return os.path.join(os.path.dirname(__file__), "working_deployments.json")


def _ordered(names: Iterable[str]) -> List[str]:
    seen = set()
    unique = []
    for name in names:
        if name and name not in seen:
            seen.add(name)
            unique.append(name)

    order = {name: idx for idx, name in enumerate(MODEL_ORDER)}
    return sorted(unique, key=lambda name: (order.get(name, len(order)), name.lower()))


def _legacy_models(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    models = []
    for name in data.get("azure_deployment_path", []):
        models.append({"name": name, "route": AZURE_OPENAI_CHAT, "works": True})
    for name in data.get("ai_inference_path", []):
        models.append({"name": name, "route": AZURE_AI_INFERENCE, "works": True})
    for name in data.get("responses_path", []):
        models.append({"name": name, "route": AZURE_OPENAI_RESPONSES, "works": True})

    # Older probe output only had a flat "working" list. Treat those as chat
    # deployments and merge with defaults so special routes are not lost.
    for name in data.get("working", []):
        models.append({"name": name, "route": AZURE_OPENAI_CHAT, "works": True})

    if not models:
        models = DEFAULT_MODELS[:]

    by_name = {model["name"]: dict(model) for model in DEFAULT_MODELS}
    for model in models:
        by_name[model["name"]] = {**by_name.get(model["name"], {}), **model}
    return list(by_name.values())


def load_registry(path: Optional[str] = None) -> Dict[str, Any]:
    path = path or registry_path()
    if not os.path.exists(path):
        return {"models": DEFAULT_MODELS[:], "source": "defaults"}

    with open(path, "r") as f:
        data = json.load(f)

    if "models" not in data:
        data["models"] = _legacy_models(data)
    return data


def get_models(include_unsupported: bool = False) -> List[Dict[str, Any]]:
    models = load_registry().get("models", [])
    if include_unsupported:
        return models
    return [
        model
        for model in models
        if model.get("route") != UNSUPPORTED and model.get("works", True)
    ]


def get_benchmark_models() -> List[str]:
    env_models = os.getenv("FRAI_MODELS")
    if env_models:
        return _ordered(name.strip() for name in env_models.split(","))

    include_openrouter = os.getenv("FRAI_INCLUDE_OPENROUTER") == "1"
    models = [
        model["name"]
        for model in get_models()
        if model.get("route")
        in {AZURE_OPENAI_CHAT, AZURE_AI_INFERENCE, AZURE_OPENAI_RESPONSES}
    ]
    if include_openrouter:
        models.extend(model["name"] for model in OPENROUTER_RECOMMENDED_MODELS)
    return _ordered(models)


def get_generator_models() -> List[str]:
    env_models = os.getenv("FRAI_GENERATOR_MODELS")
    if env_models:
        return _ordered(name.strip() for name in env_models.split(","))
    return get_benchmark_models()


def get_model_route(name: str) -> str:
    for model in get_models(include_unsupported=True):
        if model.get("name") == name:
            return model.get("route", AZURE_OPENAI_CHAT)

    for model in DEFAULT_MODELS:
        if model["name"] == name:
            return model["route"]
    for model in OPENROUTER_RECOMMENDED_MODELS + OPENROUTER_PREMIUM_MODELS:
        if model["name"] == name:
            return model["route"]
    if "/" in name:
        return OPENROUTER_CHAT
    return AZURE_OPENAI_CHAT


def get_openrouter_recommended_models() -> List[str]:
    return _ordered(model["name"] for model in OPENROUTER_RECOMMENDED_MODELS)


def get_openrouter_pricing(name: str) -> Dict[str, float]:
    for model in OPENROUTER_RECOMMENDED_MODELS + OPENROUTER_PREMIUM_MODELS:
        if model["name"] == name:
            return model.get("pricing", {"prompt": 0.0, "completion": 0.0})
    return {"prompt": 0.0, "completion": 0.0}


def estimate_openrouter_cost(
    model_names: Iterable[str],
    prompts: Iterable[str],
    max_completion_tokens: int,
    runs: int = 1,
    system_prompt_tokens: int = 20,
) -> float:
    prompt_list = list(prompts)
    prompt_token_estimate = sum(max(1, len(prompt) // 4) + system_prompt_tokens for prompt in prompt_list)
    total = 0.0
    for name in model_names:
        if get_model_route(name) != OPENROUTER_CHAT:
            continue
        pricing = get_openrouter_pricing(name)
        total += runs * (
            prompt_token_estimate * pricing["prompt"]
            + len(prompt_list) * max_completion_tokens * pricing["completion"]
        )
    return total
