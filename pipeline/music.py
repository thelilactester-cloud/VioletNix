"""Pick a royalty-free track from music/ and duck it under the narration."""
import random
import subprocess

import config

EXTS = {".mp3", ".wav", ".m4a", ".ogg", ".flac"}


def pick_track():
    tracks = [p for p in config.MUSIC_DIR.glob("*") if p.suffix.lower() in EXTS]
    return random.choice(tracks) if tracks else None


def mix(narration_wav, out_wav, track=None):
    """Narration + looped, ducked music. Returns out_wav, or narration_wav if no track."""
    track = track or pick_track()
    if track is None:
        print("[music] music/ is empty; using narration only")
        return narration_wav
    graph = ("[1:a]aloop=loop=-1:size=2000000000,volume=0.5[m];"
             "[m][0:a]sidechaincompress=threshold=0.02:ratio=10:attack=20:release=400[duck];"
             "[0:a][duck]amix=inputs=2:duration=first:normalize=0,afade=t=out:st=0:d=0[a]")
    # fade the tail out over the last 1.5 s
    dur = float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
         str(narration_wav)]))
    graph = graph.replace("afade=t=out:st=0:d=0", f"afade=t=out:st={max(dur - 1.5, 0):.2f}:d=1.5")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(narration_wav), "-i", str(track),
                    "-filter_complex", graph, "-map", "[a]", str(out_wav)], check=True)
    return out_wav
