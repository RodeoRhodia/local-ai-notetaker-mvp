#!/usr/bin/env python3
"""Transcribe a 16 kHz mono WAV to a markdown transcript with faster-whisper.

Runs on Windows Python (python.exe). Output: notes/transcripts/<wav stem>.md
"""
import argparse
import time
import wave
from datetime import datetime
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel

RATE = 16000
REPO = Path(__file__).resolve().parent


def load_wav(wav: Path) -> np.ndarray:
    """Read a 16 kHz mono 16-bit WAV into float32 in [-1, 1].

    faster-whisper would hand the path to PyAV/ffmpeg, which chokes on UNC paths,
    so the samples are decoded here and passed in as an array.
    """
    with wave.open(str(wav), "rb") as w:
        rate, ch, width = w.getframerate(), w.getnchannels(), w.getsampwidth()
        frames = w.readframes(w.getnframes())
    if rate != RATE:
        raise ValueError(f"{wav.name}: expected {RATE} Hz, got {rate} Hz (no resampling here)")
    if width != 2:
        raise ValueError(f"{wav.name}: expected 16-bit samples, got {width * 8}-bit")
    x = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    return x if ch == 1 else x.reshape(-1, ch).mean(axis=1)


def ts(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def transcribe(wav: Path, model_name: str, out_dir: Path) -> Path:
    audio = load_wav(wav)
    duration = len(audio) / RATE

    print(f"Loading {model_name} (cpu, int8)...")
    model = WhisperModel(model_name, device="cpu", compute_type="int8")

    print(f"Transcribing {wav.name} ({duration:.0f}s)...")
    t0 = time.monotonic()
    segments, _info = model.transcribe(audio, language="en", beam_size=5, vad_filter=True)
    lines = []
    for seg in segments:
        line = f"[{ts(seg.start)} - {ts(seg.end)}] {seg.text.strip()}"
        print(line, flush=True)
        lines.append(line)
    elapsed = time.monotonic() - t0

    try:
        source = wav.resolve().relative_to(REPO).as_posix()
    except ValueError:
        source = str(wav.resolve())

    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{wav.stem}.md"
    body = "\n".join(lines) if lines else "(no speech detected)"
    out.write_text(
        f"# Transcript {wav.stem}\n\n"
        f"- Source: {source}\n"
        f"- Model: {model_name} (cpu, int8)\n"
        f"- Audio duration: {duration:.1f}s\n"
        f"- Transcribed in: {elapsed:.1f}s\n"
        f"- Generated: {datetime.now():%Y-%m-%d %H:%M:%S}\n\n"
        f"{body}\n",
        encoding="utf-8",
    )
    print(f"Wrote    : {out}")
    print(f"  {len(lines)} segments in {elapsed:.1f}s ({duration / elapsed:.1f}x realtime)"
          if elapsed > 0 else f"  {len(lines)} segments")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Transcribe a 16 kHz mono WAV to markdown.")
    ap.add_argument("wav", type=Path, metavar="WAV")
    ap.add_argument("--model", default="large-v3-turbo")
    a = ap.parse_args()

    if not a.wav.exists():
        print(f"[x] No such file: {a.wav}")
        return 2
    transcribe(a.wav, a.model, REPO / "notes" / "transcripts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
