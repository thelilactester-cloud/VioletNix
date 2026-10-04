"""Write an original story script, then fact-check it against Wikipedia."""
import difflib
import json
import random

import requests

import config
import llm

STYLES = [
    "a cold open in the middle of the action, then rewind to explain",
    "second person ('You are standing on the deck...') for immersion",
    "a slow mystery that withholds the key detail until the last third",
    "a countdown of mounting stakes, each sentence raising the pressure",
    "a calm, almost gentle tone that makes the shocking facts land harder",
]

PROMPT = """You write narration for VioletNix, a faceless channel of ~1-minute TRUE history tales
("Stories from the past. Lessons for today.") for TikTok, YouTube Shorts, Reels and Facebook.

Popular-right-now signals (inspiration for WHAT people care about; never copy wording):
{signals}

Already used topics (do NOT repeat): {used}

Pick ONE real, well-documented historical story that has a Wikipedia article. Tell it in this style:
{style}

Rules:
- 180-195 words of narration (it must run longer than 61 seconds when spoken), spoken English, short sentences, concrete details, no emojis.
- Sentence 1 is a hook that creates a question in the viewer's mind. Last 1-2 sentences are the lesson for today.
- Only state facts you are certain are true. If unsure of a number or date, leave it out.
- Original wording. No copied lines from any video or article.

Return JSON with exactly these keys:
topic, wikipedia_title (exact English Wikipedia article title), hook, narration (full text incl. hook and lesson),
title (max 70 chars), scene_keywords (6 short photo search phrases, visual and generic e.g. "old sailing ship storm"),
hashtags (4-6 strings without #), pinterest_keywords (comma separated string)."""

VERIFY = """You are a strict history fact-checker. Compare the narration with the Wikipedia extract.
Narration:
{narration}

Wikipedia extract for "{title}":
{extract}

List every claim in the narration that is contradicted by the extract or that you know to be false.
Claims that are merely not mentioned in the extract are fine if they are widely accepted history.
Return JSON: {{"ok": true|false, "issues": ["..."]}}"""


def wikipedia_extract(title):
    r = requests.get("https://en.wikipedia.org/w/api.php", timeout=20,
                     headers={"User-Agent": "VioletNix/1.0"}, params={
                         "action": "query", "prop": "extracts", "explaintext": 1, "exlimit": 1,
                         "redirects": 1, "titles": title, "format": "json"})
    pages = r.json().get("query", {}).get("pages", {})
    page = next(iter(pages.values()), {})
    return (page.get("extract") or "")[:6000]


def history():
    try:
        return json.loads(config.STATE_FILE.read_text())
    except (OSError, ValueError):
        return []


def used_topics():
    return [h["topic"] for h in history()]


def remember(draft):
    config.STATE_FILE.parent.mkdir(exist_ok=True)
    config.STATE_FILE.write_text(json.dumps(
        history() + [{k: draft[k] for k in ("topic", "hook", "narration")}], indent=1))


def originality_issues(draft):
    """Platforms demote repetitive, mass-produced content: reject near-duplicates and thin scripts."""
    issues, words = [], len(draft["narration"].split())
    if not 175 <= words <= 205:
        issues.append(f"narration is {words} words (need 175-205 for a 61s+ video)")
    recent = history()[-30:]
    if draft["topic"].lower() in (h["topic"].lower() for h in recent):
        issues.append("topic already used")
    if draft["hook"].lower() in (h["hook"].lower() for h in recent):
        issues.append("hook already used")
    for h in recent:
        ratio = difflib.SequenceMatcher(None, draft["narration"].lower(), h["narration"].lower()).ratio()
        if ratio > config.MAX_SIMILARITY:
            issues.append(f"too similar ({ratio:.0%}) to a previous script about {h['topic']}")
            break
    return issues


def generate(signals, attempts=3):
    used = used_topics()
    sig = "\n".join(f"- {s['title']} ({s['source']})" for s in signals[:25]) or "- (none available)"
    for n in range(attempts):
        draft = llm.ask_json(PROMPT.format(signals=sig, used=used[-60:], style=random.choice(STYLES)))
        issues = originality_issues(draft)
        if issues:
            print(f"[script] attempt {n + 1}: rejected: {issues}")
            continue
        extract = wikipedia_extract(draft.get("wikipedia_title", ""))
        if not extract:
            print(f"[script] attempt {n + 1}: no Wikipedia article for {draft.get('wikipedia_title')!r}")
            continue
        verdict = llm.ask_json(VERIFY.format(narration=draft["narration"],
                                             title=draft["wikipedia_title"], extract=extract),
                               temperature=0)
        if verdict.get("ok"):
            return draft
        print(f"[script] attempt {n + 1}: fact-check failed: {verdict.get('issues')}")
    raise RuntimeError("could not produce a verified script; nothing will be published")
