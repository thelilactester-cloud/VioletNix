"""One video, end to end: research -> script -> voice -> music -> render -> captions -> publish.

    python pipeline/run.py --slot 0730            # real run (needs API keys)
    python pipeline/run.py --slot 0730 --sample   # offline: built-in script, no LLM/research
    PUBLISH=1 python pipeline/run.py --slot 0730  # also post to the platforms with credentials
"""
import argparse
import csv
import datetime as dt
import json
import shutil
import tempfile
from pathlib import Path

import config
import music
import publish
import render
import research
import script
import voice

PLATFORMS = ["tiktok", "youtube", "instagram", "pinterest", "facebook"]
CORE_TAGS = ["history", "storytime", "lifelessons"]
TAGLINE = "📜 Stories from the past. Lessons for today."
DISCLOSURE = "🤖 AI-narrated. Photos: Pexels."


def captions(draft):
    tags = list(dict.fromkeys(CORE_TAGS + draft["hashtags"]))
    tag = lambda *extra: " ".join(f"#{t}" for t in tags + list(extra))
    hook, title = draft["hook"], draft["title"]
    wiki = "https://en.wikipedia.org/wiki/" + draft["wikipedia_title"].replace(" ", "_")
    body = (f"{hook} ✨\n\n{TAGLINE}\n\nDid you know this story?\n\n"
            f"Source: {wiki}\n{DISCLOSURE}\n\n")
    return (f"=== TIKTOK ===\n{body}{tag('fyp')}\n\n"
            f"=== YOUTUBE ===\nTITLE: {title}\n{body}{tag('shorts')}\n\n"
            f"=== INSTAGRAM ===\n{body}{tag('reels')}\n\n"
            f"=== FACEBOOK ===\n{body}{tag('reels')}\n\n"
            f"=== PINTEREST (video Pin) ===\nTITLE: {title}\n"
            f"DESCRIPTION: {hook} Did you know this story? {DISCLOSURE} Keywords: {draft['pinterest_keywords']}.\n"
            f"BOARD: Motivation & Mindset\n"), tags


def update_schedule(day, slot, files, hook, posted):
    rows, fields = [], []
    if config.SCHEDULE_CSV.exists():
        with open(config.SCHEDULE_CSV, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fields, rows = list(reader.fieldnames), list(reader)
    for col in ("date time format video caption_file hook".split() + [f"posted_{p}" for p in PLATFORMS]):
        if col not in fields:
            fields.append(col)
    rows = [r for r in rows if not (r["date"] == day and r["time"] == f"{slot[:2]}:{slot[2:]}")]
    rows.append({"date": day, "time": f"{slot[:2]}:{slot[2:]}", "format": "tale",
                 "video": files["video"], "caption_file": files["caption"], "hook": hook,
                 **{f"posted_{p}": posted.get(p, "") for p in PLATFORMS}})
    rows.sort(key=lambda r: (r["date"], r["time"]))
    with open(config.SCHEDULE_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slot", default="0730", help="HHMM, used in the file name")
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--sample", action="store_true", help="offline test with the bundled script")
    args = ap.parse_args()

    todays = 0
    if config.SCHEDULE_CSV.exists() and not args.sample:
        with open(config.SCHEDULE_CSV, newline="", encoding="utf-8") as f:
            todays = sum(1 for r in csv.DictReader(f)
                         if r["date"] == args.date and r["time"] != f"{args.slot[:2]}:{args.slot[2:]}")
    if todays >= config.MAX_PER_DAY:
        raise SystemExit(f"[run] {todays} videos already made for {args.date} "
                         f"(MAX_PER_DAY={config.MAX_PER_DAY}); stopping to avoid mass-production flags")

    if args.sample:
        draft = json.loads((Path(__file__).parent / "sample_script.json").read_text())
    else:
        draft = script.generate(research.collect())
    print(f"[run] topic: {draft['topic']}")

    out_dir = config.ROOT / args.date
    out_dir.mkdir(exist_ok=True)
    stem = f"{args.slot}-tale"
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        narration = tmp / "narration.wav"
        timings = voice.synthesize(draft["narration"], narration)
        length = render.duration(narration)
        if length < config.MIN_SECONDS - 0.5:   # video adds 0.5 s of tail
            raise SystemExit(f"[run] narration is {length:.0f}s; need {config.MIN_SECONDS}s+ for TikTok "
                             "Creator Rewards. Not rendering.")
        mixed = music.mix(narration, tmp / "mixed.wav")
        images = render.fetch_images(draft["scene_keywords"], tmp)
        silent = tmp / "silent.mp4"
        render.render_silent(images, timings, render.duration(narration) + 0.5, silent, tmp)
        render.mux(silent, mixed, out_dir / f"{stem}.mp4")
        # narration-only copy for TikTok: add a trending sound in the app
        render.mux(silent, narration, out_dir / f"{stem}-tiktok.mp4")

    text, tags = captions(draft)
    (out_dir / f"{stem}.txt").write_text(text, encoding="utf-8")
    posted = {}
    reviewed = len(script.history())
    hold = (not args.sample) and reviewed < config.REVIEW_FIRST_N
    if hold:
        print(f"[publish] review period: video {reviewed + 1} of the first {config.REVIEW_FIRST_N} "
              "is saved but NOT posted. Check facts and quality, then post by hand or lower REVIEW_FIRST_N.")
    if config.PUBLISH and not hold:
        section = lambda name: text.split(f"=== {name}", 1)[1].split("===", 1)[0].split("\n", 1)[1].strip()
        yt_desc = section("YOUTUBE").split("\n", 1)[1]
        for name, fn in (
            ("youtube", lambda: publish.youtube(out_dir / f"{stem}.mp4", draft["title"], yt_desc, tags)),
            ("tiktok", lambda: publish.tiktok_draft(out_dir / f"{stem}-tiktok.mp4")),
            ("facebook", lambda: publish.facebook_reel(out_dir / f"{stem}.mp4", section("FACEBOOK")))):
            try:
                result = fn()
                posted[name] = ("draft" if name == "tiktok" else "yes") if result else ""
                print(f"[publish] {name}: {result or 'skipped (no credentials)'}")
            except Exception as exc:
                print(f"[publish] {name} FAILED: {exc}")
    elif not config.PUBLISH:
        print("[publish] PUBLISH is not set to 1: dry run, nothing posted")

    rel = lambda p: str(Path(args.date) / p)
    update_schedule(args.date, args.slot, {"video": rel(f"{stem}.mp4"), "caption": rel(f"{stem}.txt")},
                    draft["hook"], posted)
    if not args.sample:
        script.remember(draft)
    print(f"[run] done: {out_dir / (stem + '.mp4')}")


if __name__ == "__main__":
    main()
