#!/usr/bin/env python3
"""Capture Windows system audio and transcribe it to a markdown note.

Runs on Windows Python (python.exe), typically via ./start.sh from WSL.
"""
import argparse
from pathlib import Path

from capture import capture

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "notes" / "raw"
TRANSCRIPTS = ROOT / "notes" / "transcripts"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def main() -> int:
    ap = argparse.ArgumentParser(description="Record system audio and transcribe it.")
    ap.add_argument("--seconds", type=float, default=None,
                    help="stop after N seconds (default: record until Enter is pressed)")
    ap.add_argument("--model", default="large-v3-turbo", help="faster-whisper model name")
    ap.add_argument("--wav", type=Path, default=None, help="skip capture, transcribe this WAV")
    ap.add_argument("--no-transcribe", action="store_true", help="stop after capture")
    a = ap.parse_args()

    if a.wav is not None:
        wav = a.wav if a.wav.is_absolute() else (Path.cwd() / a.wav)
    else:
        try:
            wav = capture(a.seconds, RAW)
        except RuntimeError as e:
            print(f"[x] {e}")
            return 2

    md = None
    if not a.no_transcribe:
        # Imported lazily so --no-transcribe works without faster-whisper installed.
        from transcribe import transcribe
        try:
            md = transcribe(wav, a.model, TRANSCRIPTS)
        except KeyboardInterrupt:
            print("\n[!] Transcription cancelled.")
            print(f"    Audio kept at {rel(wav)}")
            return 130

    print("Done.")
    print(f"  Audio      : {rel(wav)}")
    if md is not None:
        print(f"  Transcript : {rel(md)}")
        print("  Next       : ask your coding agent to refine it (see AGENTS.md)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
