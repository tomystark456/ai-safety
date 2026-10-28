"""Independent Ollama adaptation of Robey et al., arXiv:2310.03684.

Random character insertion over the entire last user message, followed by
majority voting on refusal signals. This is an empirical defence, not a
certified implementation or a semantic safety classifier.
"""
from __future__ import annotations

import copy
import json
import random
import re
import secrets
import string
import urllib.request

COPIES = 5
PERTURB_PERCENT = 10
REFUSAL = re.compile(r"\b(?:cannot|can't|unable|refuse|won't)\b|\bnot\s+(?:able|appropriate)\b", re.I)


def is_refusal(text):
    return bool(REFUSAL.search(text))


def perturb(text, rng, percent=PERTURB_PERCENT):
    # Apply to the whole message: the defender does not know the suffix boundary.
    count = int(len(text) * percent / 100)
    positions = set(rng.sample(range(len(text)), count))
    alphabet = string.ascii_letters + string.digits + string.punctuation + " "
    return "".join(char + (rng.choice(alphabet) if i in positions else "") for i, char in enumerate(text))


def generate(model, messages, *, endpoint="http://127.0.0.1:11434/api/chat", max_tokens=96, seed=20261027):
    payload = {"model": model, "messages": messages, "stream": False, "keep_alive": "30m",
               "options": {"temperature": 0, "num_predict": max_tokens, "seed": seed,
                           "num_ctx": 2048, "num_gpu": 99}}
    request = urllib.request.Request(endpoint, json.dumps(payload).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=180) as response:
        result = json.load(response)
    content = result.get("message", {}).get("content")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("empty_model_response")
    return result


def defend(model, messages, *, seed=None, copies=COPIES, percent=PERTURB_PERCENT, max_tokens=96, call=generate):
    if copies < 3 or copies % 2 != 1:
        raise ValueError("copies_must_be_odd_and_at_least_three")
    if not 0 <= percent <= 100 or not messages or messages[-1].get("role") != "user":
        raise ValueError("invalid_smoothing_input")
    rng = random.Random(seed if seed is not None else secrets.randbits(64))
    candidates = []
    for index in range(copies):
        variant = copy.deepcopy(messages)
        variant[-1]["content"] = perturb(variant[-1]["content"], rng, percent)
        result = call(model, variant, max_tokens=max_tokens, seed=20261027)
        candidates.append({"response": result, "refusal": is_refusal(result["message"]["content"])})
    refusal_wins = sum(c["refusal"] for c in candidates) > copies / 2
    selected = rng.choice([c for c in candidates if c["refusal"] == refusal_wins])
    return selected["response"], {"copies": copies, "percent": percent,
                                    "refusal_votes": sum(c["refusal"] for c in candidates),
                                    "selected_refusal": selected["refusal"]}, candidates
