"""Settings read from environment variables (GitHub Actions secrets in CI)."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MUSIC_DIR = ROOT / "music"
BACKGROUND_DIR = ROOT / "backgrounds"
STATE_FILE = ROOT / "state" / "history.json"
SCHEDULE_CSV = ROOT / "schedule.csv"
CACHE_DIR = ROOT / ".cache"

# --- LLM (script writing). Gemini has a free tier; Anthropic is optional. ---
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")  # gemini | anthropic
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")

# --- Research signals (all optional, all free) ---
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
SUBREDDITS = ["todayilearned", "history", "UnresolvedMysteries", "AskHistorians"]

# --- Voice (Kokoro, runs locally, free) ---
KOKORO_MODEL = os.getenv("KOKORO_MODEL", str(CACHE_DIR / "kokoro-v1.0.onnx"))
KOKORO_VOICES = os.getenv("KOKORO_VOICES", str(CACHE_DIR / "voices-v1.0.bin"))
KOKORO_VOICE = os.getenv("KOKORO_VOICE", "af_heart")

# --- Visuals ---
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")    # free key (issuance is sometimes paused)
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")  # free key, instant; photos free for commercial use

# --- Publishing (nothing is posted unless PUBLISH=1) ---
PUBLISH = os.getenv("PUBLISH") == "1"
YT_CLIENT_ID = os.getenv("YT_CLIENT_ID")
YT_CLIENT_SECRET = os.getenv("YT_CLIENT_SECRET")
YT_REFRESH_TOKEN = os.getenv("YT_REFRESH_TOKEN")
TIKTOK_ACCESS_TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN")
FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN")

# --- Monetization safeguards ---
MIN_SECONDS = 61           # TikTok Creator Rewards needs videos over 1 minute
MAX_PER_DAY = int(os.getenv("MAX_PER_DAY", "3"))      # avoid "mass-produced" content flags
REVIEW_FIRST_N = int(os.getenv("REVIEW_FIRST_N", "5"))  # first N videos are never auto-posted
MAX_SIMILARITY = 0.45      # reject scripts too close to a recent one
