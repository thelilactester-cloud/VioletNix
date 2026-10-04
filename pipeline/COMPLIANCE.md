# Monetization checklist

The pipeline enforces what it can. Thresholds and policies change: re-check each program's page now and then.

## Enforced by code
| Rule | Why | Where |
|---|---|---|
| Video runs 61 s or longer | TikTok Creator Rewards needs videos over 1 minute | `run.py` refuses to render shorter ones |
| Script is 175-205 words, new topic, new hook, under 45% similar to the last 30 scripts | "Repetitious / mass-produced" content is demonetized on YouTube, Facebook and TikTok | `script.py` |
| Facts verified against Wikipedia, fails closed | Accuracy; reports and strikes | `script.py` |
| Max 3 videos per day | Avoid mass-production patterns | `MAX_PER_DAY` |
| First 5 videos saved but not auto-posted | You check quality and facts before going live | `REVIEW_FIRST_N` |
| Only music listed in `music/LICENSES.md` | Copyright claims block monetization | `music.py` |
| AI disclosure line, source link and photo credit in every caption; YouTube's synthetic-media flag set | Platform AI-labelling rules | `run.py`, `publish.py` |
| Not made for kids; vertical, no watermarks, no reposted clips | Ad eligibility; originality | `publish.py`, `render.py` |

## Things only you can do
- **TikTok:** turn on the "AI-generated content" label when you publish the draft, and add a trending sound
  from the *commercial-use* list only (Creative Center -> Trends -> Songs).
- **Meta:** use the "AI info" label if Facebook offers it for the Reel.
- **All platforms:** be 18+ (or use a guardian for AdSense), use real account details, enable two-factor
  authentication, set up payments and tax info when a program unlocks.
- **Thresholds to reach** (approximate, verify): YouTube 1,000 subscribers + 4,000 watch hours or 10M Shorts
  views in 90 days; TikTok 10,000 followers + 100,000 views in 30 days; Facebook, see Business Suite -> Monetization.
- **Add your own touch** over time (a recurring intro line, a consistent style, comment replies). Channels that
  look like a person's curated series survive review better than anonymous bulk output.
- **Read the first 5 videos** before letting the pipeline post by itself, and respond to any
  "limited ads" or policy notices on a platform.

Nobody can guarantee approval: the platforms decide. These rules remove the usual causes of rejection.
