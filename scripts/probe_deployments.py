"""Probe Azure text deployments and write scripts/working_deployments.json."""

import json
import os
import subprocess
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Tuple
from dotenv import load_dotenv
from openai import AzureOpenAI
from model_registry import (
    AZURE_AI_INFERENCE,
    AZURE_OPENAI_CHAT,
    AZURE_OPENAI_RESPONSES,
    DEFAULT_MODELS,
    UNSUPPORTED,
)

load_dotenv()

API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
RAW_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
if not API_KEY or not RAW_ENDPOINT:
    raise SystemExit("Missing AZURE_OPENAI_API_KEY or AZURE_OPENAI_ENDPOINT.")
ENDPOINT = RAW_ENDPOINT.rstrip("/")
API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
RESPONSES_API_VERSION = os.getenv("AZURE_OPENAI_RESPONSES_API_VERSION", "2025-04-01-preview")

client = AzureOpenAI(api_key=API_KEY, api_version=API_VERSION, azure_endpoint=ENDPOINT)
responses_client = AzureOpenAI(
    api_key=API_KEY,
    api_version=RESPONSES_API_VERSION,
    azure_endpoint=ENDPOINT,
)


def run_az(args: list[str]) -> list[dict]:
    proc = subprocess.run(
        ["az"] + args,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(proc.stdout)


def normalize_url(value: Optional[str]) -> str:
    return (value or "").replace(".openai.azure.com", ".cognitiveservices.azure.com").rstrip("/")


def find_account() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    rg = os.getenv("AZURE_OPENAI_RESOURCE_GROUP")
    account = os.getenv("AZURE_OPENAI_ACCOUNT_NAME")
    if rg and account:
        return rg, account, os.getenv("AZURE_SUBSCRIPTION_ID")

    try:
        accounts = run_az(["cognitiveservices", "account", "list"])
    except Exception as e:
        print(f"⚠️  Azure CLI discovery skipped: {e}")
        return None, None, None

    target = normalize_url(ENDPOINT)
    for item in accounts:
        endpoints = item.get("properties", {}).get("endpoints", {}) or {}
        candidates = [item.get("properties", {}).get("endpoint")] + list(endpoints.values())
        if any(normalize_url(url) == target for url in candidates):
            return item.get("resourceGroup"), item.get("name"), None
    return None, None, None


def deployment_route(deployment: dict) -> str:
    props = deployment.get("properties", {})
    caps = props.get("capabilities", {}) or {}
    model = props.get("model", {}) or {}
    model_format = model.get("format")
    if caps.get("chatCompletion") == "true" and model_format == "Mistral AI":
        return AZURE_AI_INFERENCE
    if caps.get("chatCompletion") == "true":
        return AZURE_OPENAI_CHAT
    if caps.get("responses") == "true":
        return AZURE_OPENAI_RESPONSES
    return UNSUPPORTED


def public_capabilities(capabilities: dict) -> dict:
    return {
        key: value
        for key, value in capabilities.items()
        if not key.startswith("_")
    }


def list_deployments_from_management() -> tuple[list[dict], dict]:
    rg, account, subscription = find_account()
    if not rg or not account:
        return [], {}

    deployments = run_az(["cognitiveservices", "account", "deployment", "list", "-g", rg, "-n", account])
    models = []
    for item in deployments:
        props = item.get("properties", {})
        model = props.get("model", {}) or {}
        caps = props.get("capabilities", {}) or {}
        models.append({
            "name": item["name"],
            "route": deployment_route(item),
            "format": model.get("format"),
            "model_name": model.get("name"),
            "version": model.get("version"),
            "capabilities": public_capabilities(caps),
            "provisioning_state": props.get("provisioningState"),
            "works": props.get("provisioningState") == "Succeeded",
        })
    resource = {"resource_group": rg, "account": account}
    if subscription:
        resource["subscription"] = subscription
    return models, resource


def list_chat_models() -> list[str]:
    url = f"{ENDPOINT}/openai/models?api-version={API_VERSION}"
    req = urllib.request.Request(url, headers={"api-key": API_KEY})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())
    out = []
    for m in data["data"]:
        caps = m.get("capabilities", {})
        if caps.get("chat_completion") or caps.get("completion"):
            out.append(m["id"])
    return out


def probe(model: dict) -> dict:
    """Returns (model_id, works, info)."""
    model_id = model["name"]
    route = model.get("route", AZURE_OPENAI_CHAT)
    if route == UNSUPPORTED:
        return {**model, "works": False, "probe_info": "unsupported for text benchmark"}

    try:
        if route == AZURE_OPENAI_RESPONSES:
            responses_client.responses.create(
                model=model_id,
                input="Reply with the single word ok.",
                max_output_tokens=128,
            )
            return {**model, "works": True, "probe_info": "responses"}

        if route == AZURE_AI_INFERENCE:
            url = f"{ENDPOINT}/models/chat/completions?api-version=2024-05-01-preview"
            payload = {
                "model": model_id,
                "messages": [{"role": "user", "content": "Reply with the single word ok."}],
                "max_tokens": 32,
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode(),
                headers={"api-key": API_KEY, "Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=60) as r:
                json.loads(r.read())
            return {**model, "works": True, "probe_info": "ai_inference"}

        try:
            client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": "Reply with the single word 'ok'."}],
                max_completion_tokens=128,
                temperature=0,
            )
        except Exception as e:
            msg = str(e).lower()
            if "temperature" in msg and "unsupported" in msg:
                client.chat.completions.create(
                    model=model_id,
                    messages=[{"role": "user", "content": "Reply with the single word 'ok'."}],
                    max_completion_tokens=128,
                )
            else:
                raise
        return {**model, "works": True, "probe_info": "chat"}
    except Exception as e:
        msg = str(e)
        return {**model, "works": False, "probe_info": msg[:300]}


def main():
    deployment_models, azure_resource = list_deployments_from_management()
    if deployment_models:
        models = deployment_models
        print(f"Discovered {len(models)} Azure deployments from the management API.")
    else:
        model_ids = list_chat_models()
        seeded = [model["name"] for model in DEFAULT_MODELS]
        names = sorted(set(model_ids + seeded))
        models = [
            next((dict(default) for default in DEFAULT_MODELS if default["name"] == name), {"name": name, "route": AZURE_OPENAI_CHAT})
            for name in names
        ]
        print(f"Discovered {len(models)} candidate model IDs. Probing...")

    results = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(probe, m): m for m in models}
        for i, fut in enumerate(as_completed(futures), 1):
            result = fut.result()
            tag = "OK" if result["works"] else "--"
            print(f"  [{i:3}/{len(models)}] {tag} {result['name']}  {result.get('probe_info', '')[:90]}")
            results.append(result)

    working = sorted([r["name"] for r in results if r["works"] and r["route"] != UNSUPPORTED])
    chat = sorted([r["name"] for r in results if r["works"] and r["route"] == AZURE_OPENAI_CHAT])
    ai_inference = sorted([r["name"] for r in results if r["works"] and r["route"] == AZURE_AI_INFERENCE])
    responses = sorted([r["name"] for r in results if r["works"] and r["route"] == AZURE_OPENAI_RESPONSES])
    unsupported = sorted([r["name"] for r in results if not r["works"] or r["route"] == UNSUPPORTED])

    output = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "endpoint": ENDPOINT,
        "api_version": API_VERSION,
        "responses_api_version": RESPONSES_API_VERSION,
        "azure_resource": azure_resource,
        "benchmark_models": working,
        "azure_deployment_path": chat,
        "ai_inference_path": ai_inference,
        "responses_path": responses,
        "unsupported": unsupported,
        "models": sorted(results, key=lambda item: item["name"].lower()),
    }

    out_dir = os.path.dirname(__file__)
    with open(os.path.join(out_dir, "working_deployments.json"), "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nWorking text deployments: {len(working)} / {len(models)}")
    print("Saved → scripts/working_deployments.json")


if __name__ == "__main__":
    main()
