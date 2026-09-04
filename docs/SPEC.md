# MVP Spec

**What it is:** A local CLI that records your laptop's system audio during a call and drops a timestamped markdown transcript on disk. You paste it into Claude.

**Stack**
- Python 3.11+
- `PyAudioWPatch`: WASAPI loopback capture
- `faster-whisper`: `large-v3-turbo`, `device="cpu"`, `compute_type="int8"`
- `numpy` + `soxr`: 48kHz stereo to 16kHz mono
- `start.sh`: launcher (calls Windows `python.exe` from WSL)

**Input:** Whatever is playing through your default speakers.
**Output:** `./notes/2026-09-06_1430.md`: timestamped transcript, plus the raw WAV chunks kept for debugging.
**Interface:** Run `./start.sh`, join your call, Ctrl+C when done. Console prints each chunk as it transcribes.

**Testable MVP (definition of done)**
Play a 5-minute YouTube video, run it, get a markdown file that's ~90% accurate with roughly correct timestamps. If you can paste that into Claude and get usable notes back, you're done.

# Timeline

**Fri Sep 4, evening**
Capture only. Record 30s of system audio to a clean 16kHz mono WAV that plays back correctly in VLC. Ship nothing else tonight.

**Sat Sep 5, morning**
Wire in faster-whisper. `tiny.en` first to prove the pipeline, then swap to `large-v3-turbo`. One WAV in, text out.

**Sat Sep 5, afternoon**
Chunking loop + markdown writer. Full end-to-end run on a real YouTube video.

**Sun Sep 6**
Buffer. Fix whatever broke, run it on one real call, stop.

**Explicitly out of scope:** your own mic, speaker labels, live display, .exe packaging, GUI, Claude API integration, filtering out Spotify.
