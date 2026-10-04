"""Narration with Kokoro (free, local). Sentence-by-sentence for natural pacing."""
import re
import urllib.request
from pathlib import Path

import numpy as np
import soundfile as sf

import config

MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"


def ensure_models():
    config.CACHE_DIR.mkdir(exist_ok=True)
    for path in (config.KOKORO_MODEL, config.KOKORO_VOICES):
        if not Path(path).exists():
            print(f"[voice] downloading {Path(path).name}")
            urllib.request.urlretrieve(MODEL_URL + Path(path).name, path)


def split_sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


def synthesize(narration, out_wav):
    """Write narration to out_wav. Returns [(sentence, start_s, end_s)] for captions."""
    from kokoro_onnx import Kokoro
    ensure_models()
    kokoro = Kokoro(config.KOKORO_MODEL, config.KOKORO_VOICES)
    sentences = split_sentences(narration)
    parts, timings, t, sr = [], [], 0.0, 24000
    for i, s in enumerate(sentences):
        last = i == len(sentences) - 1
        speed = 0.92 if (i == 0 or last) else 1.0   # hook and lesson are delivered slower
        samples, sr = kokoro.create(s, voice=config.KOKORO_VOICE, speed=speed, lang="en-us")
        pause = 0.7 if i == 0 else 0.45 if s.endswith(("?", "!")) else 0.3
        timings.append((s, t, t + len(samples) / sr))
        parts += [samples, np.zeros(int(pause * sr), dtype=samples.dtype)]
        t += len(samples) / sr + pause
    sf.write(out_wav, np.concatenate(parts), sr)
    return timings
