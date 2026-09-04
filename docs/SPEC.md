# MVP Spec

**What it is:** A local CLI that records your laptop's system audio during a call and drops a timestamped markdown transcript on disk. You paste it into Claude.

**Stack**
- Python 3.11+
- `PyAudioWPatch`: WASAPI loopback capture
- `faster-whisper`: default `large-v3-turbo`, `device="cpu"`, `compute_type="int8"`; `tiny.en` for fast sanity checks
- `numpy` + `soxr`: 48kHz stereo to 16kHz mono
- `notetaker.py`: entry point, records then transcribes
- `capture.py`: WASAPI loopback recording to WAV
- `transcribe.py`: faster-whisper transcription to markdown
- `start.sh`: launcher (calls Windows `python.exe` from WSL)

**Input:** Whatever is playing through your default speakers.
**Output:** `notes/raw/YYYY-MM-DD_HHMMSS.wav` (16kHz mono WAV) and `notes/transcripts/YYYY-MM-DD_HHMMSS.md` (timestamped transcript), same timestamp, both kept on disk.
**Interface:** Run `./start.sh`, join your call, press Enter when done to stop recording and start transcription. Flags: `--seconds N`, `--model NAME`, `--wav PATH`, `--no-transcribe`.

**Testable MVP (definition of done)**
Play a 5-minute YouTube video, run it, get a markdown file that's ~90% accurate with roughly correct timestamps. If you can paste that into Claude and get usable notes back, you're done.

# Timeline

**Fri Sep 4, evening: DONE**
Capture only. Record 30s of system audio to a clean 16kHz mono WAV that plays back correctly in VLC. Ship nothing else tonight.

**Sat Sep 5, morning: DONE**
Wire in faster-whisper. `tiny.en` first to prove the pipeline, then swap to `large-v3-turbo`. One WAV in, text out.

**Sat Sep 5, afternoon**
Single-command record-then-transcribe pipeline: `./start.sh` records until Enter is pressed, then transcribes automatically and writes a markdown transcript with timestamps. Chunking loop moved out; transcription runs once, after recording ends.

**Sun Sep 6**
Buffer. Fix whatever broke, run it on one real call, stop. Optional: live chunked transcription during the call.

**Explicitly out of scope:** your own mic, speaker labels, live display, .exe packaging, GUI, Claude API integration, filtering out Spotify.
