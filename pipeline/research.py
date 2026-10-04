"""Collect popular-story signals. Every source is free and optional."""
import datetime as dt

import requests

import config

UA = {"User-Agent": "VioletNix/1.0 (history story research)"}


def reddit_top(limit=10):
    if not (config.REDDIT_CLIENT_ID and config.REDDIT_CLIENT_SECRET):
        return []
    auth = (config.REDDIT_CLIENT_ID, config.REDDIT_CLIENT_SECRET)
    tok = requests.post("https://www.reddit.com/api/v1/access_token",
                        auth=auth, data={"grant_type": "client_credentials"},
                        headers=UA, timeout=20).json().get("access_token")
    if not tok:
        return []
    headers = {**UA, "Authorization": f"bearer {tok}"}
    out = []
    for sub in config.SUBREDDITS:
        r = requests.get(f"https://oauth.reddit.com/r/{sub}/top",
                         params={"t": "week", "limit": limit}, headers=headers, timeout=20)
        for p in r.json().get("data", {}).get("children", []):
            d = p["data"]
            out.append({"source": f"reddit/r/{sub}", "title": d["title"], "score": d["score"]})
    return out


def wikipedia_on_this_day(today=None):
    today = today or dt.date.today()
    url = f"https://api.wikimedia.org/feed/v1/wikipedia/en/onthisday/events/{today:%m}/{today:%d}"
    r = requests.get(url, headers=UA, timeout=20)
    if r.status_code != 200:
        return []
    out = []
    for e in r.json().get("events", [])[:25]:
        pages = e.get("pages") or [{}]
        out.append({"source": "wikipedia/on-this-day", "title": f"{e['year']}: {e['text']}",
                    "score": len(pages), "wikipedia_title": pages[0].get("title")})
    return out


def youtube_popular(limit=10):
    """Most-viewed recent short history videos: shows which hooks are working."""
    if not config.YOUTUBE_API_KEY:
        return []
    since = (dt.datetime.utcnow() - dt.timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    r = requests.get("https://www.googleapis.com/youtube/v3/search", timeout=20, params={
        "part": "snippet", "q": "history story shorts", "type": "video",
        "videoDuration": "short", "order": "viewCount", "publishedAfter": since,
        "maxResults": limit, "key": config.YOUTUBE_API_KEY})
    return [{"source": "youtube/popular", "title": i["snippet"]["title"], "score": 0}
            for i in r.json().get("items", [])]


def collect():
    signals = []
    for fn in (reddit_top, wikipedia_on_this_day, youtube_popular):
        try:
            signals += fn()
        except Exception as exc:  # one dead source must not stop the run
            print(f"[research] {fn.__name__} failed: {exc}")
    signals.sort(key=lambda s: s["score"], reverse=True)
    return signals
