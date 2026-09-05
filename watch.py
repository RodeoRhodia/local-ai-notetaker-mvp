#!/usr/bin/env python3
"""Wait for a fresh transcript to land in notes/transcripts/ and print its path.

The recorder (./start.sh) writes notes/transcripts/<stem>.md on the Windows side.
This watcher runs on Linux, blocks until a transcript that still needs refining
appears and has finished being written, then prints its absolute path on stdout
so a coding agent can pick it up. Stdout stays clean: the path is the only thing
ever written there.

A transcript is "pending" when notes/refined/<stem>.md does not exist yet. By
default only transcripts modified after the watcher started are reported, so an
old unrefined file cannot hijack a new session; --any lifts that restriction.

Exit codes: 0 a path was printed, 3 timed out, 130 interrupted with Ctrl+C.
"""
import argparse
import sys
import time
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent
TRANSCRIPTS = ROOT / "notes" / "transcripts"
REFINED = ROOT / "notes" / "refined"
SUMMARIES = ROOT / "notes" / "summaries"


def newest_pending(cutoff: float) -> Optional[Path]:
    """Newest transcript with no refined counterpart, modified after cutoff.

    The glob is *.md, so half written files named <stem>.md.tmp are skipped
    already; the explicit suffix check keeps that guarantee if the glob changes.
    """
    best: Optional[Path] = None
    best_mtime = 0.0
    for path in TRANSCRIPTS.glob("*.md"):
        if path.name.endswith(".tmp") or not path.is_file():
            continue
        if (REFINED / path.name).exists():
            continue
        mtime = path.stat().st_mtime
        if mtime <= cutoff or mtime < best_mtime:
            continue
        best, best_mtime = path, mtime
    return best


def main() -> int:
    ap = argparse.ArgumentParser(description="Wait for a new transcript and print its path.")
    ap.add_argument("--timeout", type=float, default=None,
                    help="give up after N seconds (default: wait forever)")
    ap.add_argument("--any", action="store_true", dest="any_",
                    help="also accept a transcript that predates this watcher")
    ap.add_argument("--interval", type=float, default=2.0, help="seconds between polls")
    a = ap.parse_args()

    for directory in (TRANSCRIPTS, REFINED, SUMMARIES):
        directory.mkdir(parents=True, exist_ok=True)

    started = time.time()
    cutoff = 0.0 if a.any_ else started
    deadline = started + a.timeout if a.timeout is not None else None

    if not (a.any_ and newest_pending(cutoff) is not None):
        print("Waiting for a new transcript in notes/transcripts/ ...", file=sys.stderr)

    sizes: dict[Path, int] = {}
    while True:
        candidate = newest_pending(cutoff)
        if candidate is not None:
            size = candidate.stat().st_size
            # Ready only once the size has held steady across two polls.
            if size > 0 and sizes.get(candidate) == size:
                print(candidate.resolve())
                return 0
            sizes[candidate] = size
        now = time.time()
        if deadline is not None and now >= deadline:
            print(f"Timed out after {a.timeout:g} s, run again", file=sys.stderr)
            return 3
        nap = a.interval if deadline is None else min(a.interval, deadline - now)
        time.sleep(max(nap, 0.0))


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
