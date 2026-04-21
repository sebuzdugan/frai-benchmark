"""Unified Azure model client.

This single endpoint hosts models that speak three different protocols:
1. The "Azure OpenAI" deployment path (`/openai/deployments/<name>/chat/completions`)
   — used by gpt-*, DeepSeek, grok, Kimi.
2. The "Azure AI Inference" path (`/models/chat/completions`) with the model name
   in the JSON body — used by Mistral-Large-3.
3. The Azure OpenAI Responses API (`/openai/responses`) — used by Responses-only
   deployments such as gpt-5.4-pro and gpt-5.2-codex.

We also gracefully handle:
  - reasoning models that reject custom `temperature`,
  - models that require `max_tokens` instead of `max_completion_tokens`,
  - Azure content filter blocks (return a sentinel string),
  - rate-limit retries with exponential backoff.
"""

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Optional

from dotenv import load_dotenv
from openai import APIError, AzureOpenAI, RateLimitError
from openai import OpenAI
from model_registry import (
    AZURE_AI_INFERENCE,
    AZURE_OPENAI_RESPONSES,
    OPENROUTER_CHAT,
    get_model_route,
)

load_dotenv()


CONTENT_FILTER_SENTINEL = "Azure Content Filter triggered: The request was blocked due to safety policies."

# Models that reject the `temperature` parameter (reasoning + chat-tuned variants)
NO_TEMPERATURE_MODELS = {
    "gpt-5.4-pro",
    "gpt-5.2",
    "gpt-5.2-chat",
    "gpt-5.2-codex",
    "o1", "o1-mini", "o3", "o3-mini", "o4-mini",
}


class LLMClient:
    def __init__(self, deployment_name: Optional[str] = None):
        self.deployment_name = deployment_name or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        if not self.deployment_name:
            raise ValueError("Missing deployment name. Set FRAI_MODELS or AZURE_OPENAI_DEPLOYMENT_NAME.")
        self.route = get_model_route(self.deployment_name)

        self.uses_ai_inference = self.route == AZURE_AI_INFERENCE
        self.uses_responses = self.route == AZURE_OPENAI_RESPONSES
        self.uses_openrouter = self.route == OPENROUTER_CHAT

        self.openai_client = None
        self.responses_client = None
        self.openrouter_client = None

        if self.uses_openrouter:
            self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
            if not self.openrouter_api_key:
                raise ValueError("Missing OPENROUTER_API_KEY for OpenRouter model.")
            self.openrouter_client = OpenAI(
                api_key=self.openrouter_api_key,
                base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
                default_headers={
                    "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", "https://github.com/sebuzdugan/frai-benchmark"),
                    "X-Title": os.getenv("OPENROUTER_APP_NAME", "FRAI Benchmark"),
                },
            )
        else:
            self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
            raw_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            if not self.api_key or not raw_endpoint:
                raise ValueError("Missing AZURE_OPENAI_API_KEY or AZURE_OPENAI_ENDPOINT.")

            self.endpoint = raw_endpoint.rstrip("/")
            self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
            self.responses_api_version = os.getenv(
                "AZURE_OPENAI_RESPONSES_API_VERSION", "2025-04-01-preview"
            )
            self.openai_client = AzureOpenAI(
                api_key=self.api_key,
                api_version=self.api_version,
                azure_endpoint=self.endpoint,
            )
            self.responses_client = AzureOpenAI(
                api_key=self.api_key,
                api_version=self.responses_api_version,
                azure_endpoint=self.endpoint,
            )

    # ----- public --------------------------------------------------------

    def generate_response(
        self,
        prompt: str,
        system_prompt: str = "You are a helpful AI assistant.",
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        max_retries = 5
        current_temp = temperature

        for attempt in range(max_retries):
            try:
                if self.uses_openrouter:
                    return self._call_openrouter(system_prompt, prompt, current_temp, max_tokens)
                if self.uses_responses:
                    return self._call_azure_responses(system_prompt, prompt, max_tokens)
                if self.uses_ai_inference:
                    return self._call_ai_inference(
                        system_prompt, prompt, current_temp, max_tokens
                    )
                return self._call_azure_openai(
                    system_prompt, prompt, current_temp, max_tokens
                )

            except RateLimitError:
                if attempt < max_retries - 1:
                    wait = (attempt + 1) * 5
                    print(f"⏳ Rate limit. Retrying in {wait}s...")
                    time.sleep(wait)
                    continue
                raise

            except APIError as e:
                msg = str(e).lower()
                code = getattr(e, "code", None)
                body = getattr(e, "body", None) or {}
                if code == "content_filter" or (isinstance(body, dict) and body.get("code") == "content_filter"):
                    return CONTENT_FILTER_SENTINEL
                if "temperature" in msg and "unsupported" in msg:
                    current_temp = None
                    continue
                if "max_tokens" in msg and "not supported" in msg:
                    # Some models want max_completion_tokens; the SDK already uses
                    # that, so this branch indicates the *opposite*: switch to AI Inference.
                    self.uses_ai_inference = True
                    continue
                if "operationnot supported" in msg or "operation not supported" in msg:
                    self.uses_responses = True
                    continue
                raise

            except urllib.error.HTTPError as e:
                body = e.read().decode(errors="replace")
                if e.code == 429 and attempt < max_retries - 1:
                    wait = (attempt + 1) * 5
                    print(f"⏳ Rate limit (HTTP 429). Retrying in {wait}s...")
                    time.sleep(wait)
                    continue
                if "content_filter" in body.lower():
                    return CONTENT_FILTER_SENTINEL
                raise RuntimeError(f"AI-Inference HTTP {e.code}: {body[:300]}")

        return ""

    # ----- private -------------------------------------------------------

    def _call_azure_openai(self, system_prompt, prompt, temperature, max_tokens):
        if self.openai_client is None:
            raise RuntimeError("Azure OpenAI client is not initialized.")
        kwargs = dict(
            model=self.deployment_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            max_completion_tokens=max_tokens,
        )
        if temperature is not None and self.deployment_name not in NO_TEMPERATURE_MODELS:
            kwargs["temperature"] = temperature
        resp = self.openai_client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content or ""

    def _call_azure_responses(self, system_prompt, prompt, max_tokens):
        if self.responses_client is None:
            raise RuntimeError("Azure Responses client is not initialized.")
        resp = self.responses_client.responses.create(
            model=self.deployment_name,
            instructions=system_prompt,
            input=prompt,
            max_output_tokens=max_tokens,
        )
        return getattr(resp, "output_text", None) or self._extract_response_text(resp)

    def _extract_response_text(self, response: Any) -> str:
        chunks = []
        for item in getattr(response, "output", []) or []:
            for content in getattr(item, "content", []) or []:
                text = getattr(content, "text", None)
                if text:
                    chunks.append(text)
        return "\n".join(chunks)

    def _call_ai_inference(self, system_prompt, prompt, temperature, max_tokens):
        url = f"{self.endpoint}/models/chat/completions?api-version=2024-05-01-preview"
        payload = {
            "model": self.deployment_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={"api-key": self.api_key, "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read())
        return data["choices"][0]["message"]["content"] or ""

    def _call_openrouter(self, system_prompt, prompt, temperature, max_tokens):
        if self.openrouter_client is None:
            raise RuntimeError("OpenRouter client is not initialized.")
        kwargs = {
            "model": self.deployment_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens,
        }
        if temperature is not None:
            kwargs["temperature"] = temperature
        resp = self.openrouter_client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content or ""
