#!/usr/bin/env python3
"""Record Windows system audio (WASAPI loopback) to a 16 kHz mono 16-bit WAV.

Runs on Windows Python (python.exe). Output: notes/raw/YYYY-MM-DD_HHMM.wav
"""
import argparse
import time
import wave
from datetime import datetime
from pathlib import Path

import numpy as np
import pyaudiowpatch as pyaudio
import soxr

OUT_RATE = 16000
CHUNK = 1024


def main() -> int:
    ap = argparse.ArgumentParser(description="Capture Windows system audio to a 16 kHz mono WAV.")
    ap.add_argument("pos_seconds", nargs="?", type=float, default=None, metavar="SECONDS")
    ap.add_argument("--seconds", dest="opt_seconds", type=float, default=None)
    a = ap.parse_args()
    seconds = a.opt_seconds if a.opt_seconds is not None else (a.pos_seconds or 30.0)

    p = pyaudio.PyAudio()
    try:
        dev = p.get_default_wasapi_loopback()
    except (OSError, LookupError):
        dev = next(p.get_loopback_device_info_generator(), None)
    if dev is None:
        print("[x] No WASAPI loopback device found (is an output device enabled?)")
        p.terminate()
        return 2

    rate, ch = int(dev["defaultSampleRate"]), int(dev["maxInputChannels"])
    print(f"Device  : {dev['name']}")
    print(f"Rate    : {rate} Hz")
    print(f"Channels: {ch}")
    print(f"Recording {seconds:.0f}s (Ctrl+C to stop early)...")

    # Loopback endpoints are input devices; rate/channels must match the mix format.
    stream = p.open(format=pyaudio.paFloat32, channels=ch, rate=rate,
                    input=True, input_device_index=dev["index"], frames_per_buffer=CHUNK)

    blocks, target, got = [], int(seconds * rate), 0
    t0, tick = time.monotonic(), 1.0
    try:
        while got < target:
            data = stream.read(CHUNK, exception_on_overflow=False)
            blocks.append(np.frombuffer(data, dtype=np.float32))
            got += CHUNK
            el = time.monotonic() - t0
            if el >= tick:
                print(f"\r  {el:5.1f}s / {seconds:.0f}s", end="", flush=True)
                tick += 1.0
    except KeyboardInterrupt:
        print("\n[!] Interrupted, writing what was captured.")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
    print(f"\r  {time.monotonic() - t0:5.1f}s captured.        ")

    x = np.concatenate(blocks).reshape(-1, ch)[:target] if blocks else np.zeros((0, ch), np.float32)
    mono = x.mean(axis=1)
    y = mono if rate == OUT_RATE else soxr.resample(mono, rate, OUT_RATE, quality="HQ")
    pcm = (np.clip(y, -1.0, 1.0) * 32767.0).astype(np.int16)

    out = Path(__file__).resolve().parent / "notes" / "raw" / f"{datetime.now():%Y-%m-%d_%H%M}.wav"
    out.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(OUT_RATE)
        w.writeframes(pcm.tobytes())

    rms = float(np.sqrt(np.mean(np.square(y)))) if y.size else 0.0
    print(f"Wrote   : {out}")
    print(f"  {len(pcm) / OUT_RATE:.1f}s @ {OUT_RATE} Hz mono, RMS {rms:.4f}"
          + ("  <- SILENT: was anything playing?" if rms < 1e-5 else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
