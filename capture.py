#!/usr/bin/env python3
"""Record Windows system audio (WASAPI loopback) to a 16 kHz mono 16-bit WAV.

Runs on Windows Python (python.exe). Output: notes/raw/YYYY-MM-DD_HHMMSS.wav
"""
import argparse
import threading
import time
import wave
from datetime import datetime
from pathlib import Path

import numpy as np
import pyaudiowpatch as pyaudio
import soxr

OUT_RATE = 16000
CHUNK = 1024


def capture(seconds: float | None, out_dir: Path) -> Path:
    """Record system audio to a 16 kHz mono WAV and return the written path.

    seconds=None records until the user presses Enter (or Ctrl+C).
    """
    p = pyaudio.PyAudio()
    try:
        dev = p.get_default_wasapi_loopback()
    except (OSError, LookupError):
        dev = next(p.get_loopback_device_info_generator(), None)
    if dev is None:
        p.terminate()
        raise RuntimeError("No WASAPI loopback device found (is an output device enabled?)")

    rate, ch = int(dev["defaultSampleRate"]), int(dev["maxInputChannels"])
    print(f"Device  : {dev['name']}")
    print(f"Rate    : {rate} Hz")
    print(f"Channels: {ch}")
    if seconds is None:
        print("Recording... press Enter to stop.")
    else:
        print(f"Recording {seconds:.0f}s (Enter or Ctrl+C to stop early)...")

    target = int(seconds * rate) if seconds is not None else None
    blocks, got = [], 0
    done = threading.Event()

    # Audio arrives on PortAudio's thread so the main thread never blocks on the
    # device. Loopback delivers nothing while the system is silent, so this also
    # keeps Enter/Ctrl+C responsive during silence. Downmix as we go so RAM stays
    # at ~192 KB per second of audio.
    def on_audio(in_data, frame_count, time_info, status):
        nonlocal got
        blocks.append(np.frombuffer(in_data, dtype=np.float32).reshape(-1, ch).mean(axis=1))
        got += frame_count
        if target is not None and got >= target:
            done.set()
            return None, pyaudio.paComplete
        return None, pyaudio.paContinue

    def progress():
        while not done.wait(1.0):
            print(f"\r  {got / rate:5.1f}s captured", end="", flush=True)

    # Loopback endpoints are input devices; rate/channels must match the mix format.
    stream = p.open(format=pyaudio.paFloat32, channels=ch, rate=rate,
                    input=True, input_device_index=dev["index"],
                    frames_per_buffer=CHUNK, stream_callback=on_audio)
    started = datetime.now()
    threading.Thread(target=progress, daemon=True).start()
    try:
        if target is None:
            input()
        else:
            while not done.wait(0.2):
                pass
    except (KeyboardInterrupt, EOFError):
        print("\n[!] Stopped.")
    finally:
        done.set()
        stream.stop_stream()
        stream.close()
        p.terminate()
    print(f"\r  {got / rate:5.1f}s captured.        ")

    mono = np.concatenate(blocks) if blocks else np.zeros(0, np.float32)
    if target is not None:
        mono = mono[:target]
    if mono.size == 0:
        raise RuntimeError("Nothing captured (was anything playing?)")

    y = mono if rate == OUT_RATE else soxr.resample(mono, rate, OUT_RATE, quality="HQ")
    pcm = (np.clip(y, -1.0, 1.0) * 32767.0).astype(np.int16)

    out = out_dir / f"{started:%Y-%m-%d_%H%M%S}.wav"
    out_dir.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(OUT_RATE)
        w.writeframes(pcm.tobytes())

    rms = float(np.sqrt(np.mean(np.square(y))))
    print(f"Wrote   : {out}")
    print(f"  {len(pcm) / OUT_RATE:.1f}s @ {OUT_RATE} Hz mono, RMS {rms:.4f}"
          + ("  <- SILENT: was anything playing?" if rms < 1e-5 else ""))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Capture Windows system audio to a 16 kHz mono WAV.")
    ap.add_argument("pos_seconds", nargs="?", type=float, default=None, metavar="SECONDS")
    ap.add_argument("--seconds", dest="opt_seconds", type=float, default=None)
    a = ap.parse_args()
    seconds = a.opt_seconds if a.opt_seconds is not None else a.pos_seconds

    out_dir = Path(__file__).resolve().parent / "notes" / "raw"
    try:
        capture(seconds, out_dir)
    except RuntimeError as e:
        print(f"[x] {e}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
