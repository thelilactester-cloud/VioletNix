"""Build a 1080x1920 video: slow-zoom photos, burned-in captions, audio."""
import random
import subprocess
from pathlib import Path

import requests

import config

W, H, FPS = 1080, 1920, 30
IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def duration(path):
    return float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)]))


credit = "free-licence stock photos"


def _pexels(kw, dest):
    r = requests.get("https://api.pexels.com/v1/search", timeout=20,
                     headers={"Authorization": config.PEXELS_API_KEY},
                     params={"query": kw, "orientation": "portrait", "per_page": 8})
    photos = r.json().get("photos", [])
    if not photos:
        return False
    dest.write_bytes(requests.get(random.choice(photos)["src"]["portrait"], timeout=30).content)
    return True


def _pixabay(kw, dest):
    r = requests.get("https://pixabay.com/api/", timeout=20, params={
        "key": config.PIXABAY_API_KEY, "q": kw, "orientation": "vertical", "image_type": "photo",
        "safesearch": "true", "per_page": 20, "min_height": 1200})
    hits = r.json().get("hits", [])
    if not hits:
        return False
    dest.write_bytes(requests.get(random.choice(hits)["largeImageURL"], timeout=30).content)
    return True


def fetch_images(keywords, workdir):
    """Free stock photos per scene keyword (Pexels or Pixabay); fall back to local backgrounds/."""
    global credit
    source = (("Pexels", _pexels) if config.PEXELS_API_KEY
              else ("Pixabay", _pixabay) if config.PIXABAY_API_KEY else None)
    images = []
    if source:
        for i, kw in enumerate(keywords):
            dest = Path(workdir) / f"scene{i}.jpg"
            try:
                if source[1](kw, dest):
                    images.append(dest)
            except Exception as exc:
                print(f"[render] {source[0]} '{kw}' failed: {exc}")
        if images:
            credit = f"Photos: {source[0]}"
    local = [p for p in config.BACKGROUND_DIR.glob("*") if p.suffix.lower() in IMG_EXTS]
    while len(images) < len(keywords) and local:
        images.append(random.choice(local))
    if not images:
        raise RuntimeError("no images: set PIXABAY_API_KEY (or PEXELS_API_KEY) or put photos in backgrounds/")
    return images


def _ts(t):
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def write_ass(timings, path, words_per_caption=4):
    lines = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "",
             "[V4+ Styles]",
             "Format: Name,Fontname,Fontsize,PrimaryColour,OutlineColour,BackColour,Bold,Outline,"
             "Shadow,Alignment,MarginL,MarginR,MarginV",
             "Style: Cap,DejaVu Sans,84,&H00FFFFFF,&H00000000,&H80000000,1,6,2,2,80,80,520", "",
             "[Events]", "Format: Layer,Start,End,Style,Text"]
    for sentence, start, end in timings:
        words = sentence.split()
        chunks = [words[i:i + words_per_caption] for i in range(0, len(words), words_per_caption)]
        total = sum(len(" ".join(c)) for c in chunks)
        t = start
        for c in chunks:
            d = (end - start) * len(" ".join(c)) / total
            lines.append(f"Dialogue: 0,{_ts(t)},{_ts(t + d)},Cap,{' '.join(c).upper()}")
            t += d
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def render_silent(images, timings, total, out_mp4, workdir):
    ass = Path(workdir) / "captions.ass"
    write_ass(timings, ass)
    per = total / len(images)
    frames = int(per * FPS)
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    chains = []
    for i, img in enumerate(images):
        cmd += ["-i", str(img)]
        chains.append(
            f"[{i}:v]scale={W * 2}:{H * 2}:force_original_aspect_ratio=increase,crop={W * 2}:{H * 2},"
            f"zoompan=z='min(zoom+0.0007,1.25)':d={frames}:s={W}x{H}:fps={FPS},setsar=1[v{i}]")
    concat = "".join(f"[v{i}]" for i in range(len(images)))
    graph = (";".join(chains) + f";{concat}concat=n={len(images)}:v=1:a=0,"
             f"drawbox=x=0:y=0:w=iw:h=ih:color=black@0.35:t=fill,"
             f"subtitles={ass}[v]")
    cmd += ["-filter_complex", graph, "-map", "[v]", "-r", str(FPS), "-pix_fmt", "yuv420p",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20", str(out_mp4)]
    subprocess.run(cmd, check=True)


def mux(video, audio, out_mp4):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-i", str(audio),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", str(out_mp4)], check=True)
