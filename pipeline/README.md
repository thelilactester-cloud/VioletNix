# VioletNix pipeline

Makes one ~1-minute faceless history video and (optionally) posts it. Everything it needs is free.

```
research.py  Reddit + Wikipedia "on this day" + YouTube popular  -> what people care about now
script.py    Gemini (free tier) writes an original script, varied style each time,
             then fact-checks it against the Wikipedia article. Fails closed: no verified script, no video.
voice.py     Kokoro (local, free). Sentence-by-sentence: slower hook and lesson, varied pauses
music.py     royalty-free track from music/, ducked under the voice
render.py    Pexels photos (free key) with slow zoom, burned-in word-group captions, 1080x1920
publish.py   YouTube, TikTok (as draft), Facebook Reels
run.py       runs all of the above, writes the caption file and updates schedule.csv
```

## Try it with no keys
```bash
pip install -r pipeline/requirements.txt          # needs ffmpeg + fonts-dejavu-core installed
python pipeline/run.py --sample --date 2026-01-01  # built-in script, local voice, nothing posted
```
Put a few photos in `backgrounds/` and a track in `music/` first.

## Free keys (add as GitHub repo secrets: Settings -> Secrets and variables -> Actions)
| Secret | Where | Needed? |
|---|---|---|
| `GEMINI_API_KEY` | aistudio.google.com/apikey | yes (script writing; free tier) |
| `PEXELS_API_KEY` | pexels.com/api | recommended (scene photos) |
| `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET` | reddit.com/prefs/apps (script type) | optional |
| `YOUTUBE_API_KEY` | Google Cloud Console, YouTube Data API v3 | optional (trend research) |
| `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN` | OAuth client for YouTube upload | for auto-posting to YouTube |
| `TIKTOK_ACCESS_TOKEN` | developers.tiktok.com, Content Posting API | for TikTok drafts |
| `FB_PAGE_ID`, `FB_PAGE_TOKEN` | developers.facebook.com, a Page you manage | for Facebook Reels |

Nothing is posted unless `PUBLISH=1`. The scheduled workflow sets it; manual runs default to a dry run.
A platform without credentials is skipped, not an error.

## Trending sounds (TikTok)
TikTok's API cannot attach a library sound, and baking a chart song into the file gets it muted or
claimed on other platforms. So:
1. `publish.py` uploads `*-tiktok.mp4` (narration only, no music) to your **TikTok drafts**.
2. Open TikTok, open the draft, tap **Add sound**, choose a trending track (check TikTok's Creative
   Center -> Trends -> Songs, filtered to commercial-use), lower its volume under the voice, publish.
3. YouTube and Facebook get the royalty-free-music version, so they never trip copyright claims.

## Instagram and Pinterest
Posted by hand from `schedule.csv` (their APIs need business accounts and app review). Caption text for
each platform is in the video's `.txt` file.

## Tips
- Label AI voice and AI-assisted content when the platform asks (YouTube sets it automatically here).
- Vary hooks and styles; platforms demote near-identical mass-produced videos. The prompt already rotates styles.
- Review the first few scripts yourself before leaving it fully automatic.
- Videos are committed to the repo (about 1.5 MB each); move to release assets or cloud storage if size grows.
