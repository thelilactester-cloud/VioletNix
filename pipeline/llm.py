"""Minimal LLM client: Gemini (free tier) or Anthropic. Returns parsed JSON."""
import json
import re

import requests

import config


def _parse(text):
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    return json.loads(text)


def ask_json(prompt, temperature=1.0):
    if config.LLM_PROVIDER == "anthropic":
        if not config.ANTHROPIC_API_KEY:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        r = requests.post("https://api.anthropic.com/v1/messages", timeout=120, headers={
            "x-api-key": config.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01"},
            json={"model": config.ANTHROPIC_MODEL, "max_tokens": 2000,
                  "temperature": min(temperature, 1.0),
                  "messages": [{"role": "user", "content": prompt}]})
        r.raise_for_status()
        return _parse(r.json()["content"][0]["text"])
    if not config.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set (free key: https://aistudio.google.com/apikey)")
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           f"{config.GEMINI_MODEL}:generateContent")
    r = requests.post(url, timeout=120, headers={"x-goog-api-key": config.GEMINI_API_KEY}, json={
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature, "responseMimeType": "application/json"}})
    r.raise_for_status()
    return _parse(r.json()["candidates"][0]["content"]["parts"][0]["text"])
