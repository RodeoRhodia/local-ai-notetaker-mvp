# Local AI Notetaker MVP

Records whatever is playing through your Windows speakers, then transcribes it locally with faster-whisper. Nothing leaves your machine except the one-time model download. A coding agent then turns the transcript into clean notes; see [AGENTS.md](AGENTS.md).

Current phase: record, transcribe, agent refinement. See [docs/SPEC.md](docs/SPEC.md).

## Requirements

- Windows 11 with WSL2 (Ubuntu) installed. The repo lives and runs from a WSL shell.
- Windows Python 3.11+ on the Windows side, callable from WSL as `python.exe` (Microsoft Store Python works).
- An enabled audio output device (speakers or headphones).
- VLC or any audio player, to check the recording.
- 8 GB RAM minimum, 16 GB recommended for the `large-v3-turbo` model.

WSL itself has no audio devices. The script always runs with Windows Python; WSL is just where you type the commands.

## Install

From a WSL shell:

```bash
git clone https://github.com/RodeoRhodia/local-ai-notetaker-mvp.git
cd local-ai-notetaker-mvp
REQ="$(wslpath -w "$PWD/requirements.txt")"
(cd /mnt/c && python.exe -m pip install --user -r "$REQ")
```

## Run

```bash
./start.sh
```

Records system audio until you press Enter, then transcribes it. Flags (passed through to `notetaker.py`):

- `--seconds N`: record a fixed length instead of until Enter.
- `--model NAME`: whisper model to use (default `large-v3-turbo`; `tiny.en` is a fast sanity-check model).
- `--wav PATH`: skip recording and transcribe an existing WAV.
- `--no-transcribe`: record only.

Press Enter to stop recording and start transcription (Ctrl+C also works in most terminals). Ctrl+C during transcription cancels it and keeps the WAV; rerun with `--wav` to transcribe later.

Transcription runs on the CPU with int8 weights. Measured on an Intel Core Ultra 7 155H: large-v3-turbo runs at about 2.4x realtime, so a 30-minute call takes about 12 minutes to transcribe after you stop it; small.en is about 7x and tiny.en about 13x. The first run with a given model downloads it from Hugging Face into `%USERPROFILE%\.cache\huggingface` (`large-v3-turbo` about 1.6 GB, `tiny.en` about 75 MB); internet is needed only for that download.

## Refine with a coding agent

Open Claude Code, Codex, or any coding agent in the repo and say "Run the transcription program, which is a local ai notetaker." The agent follows [AGENTS.md](AGENTS.md): it tells you to run `./start.sh`, waits with `python3 watch.py` for the transcript, then writes `notes/refined/<stem>.md` (the cleaned transcript, cohesive, nothing dropped) and `notes/summaries/<stem>.md` (structured learning notes). If you already recorded before opening the agent, say so and it uses `python3 watch.py --any` instead of waiting for a new one.

## Output

- `notes/raw/YYYY-MM-DD_HHMMSS.wav`: 16 kHz, mono, 16-bit PCM.
- `notes/transcripts/YYYY-MM-DD_HHMMSS.md`: same timestamp, a `# Transcript <timestamp>` heading, a short metadata list (source WAV, model, audio duration, transcribe time, generated time), then one `[MM:SS - MM:SS] text` line per segment.
- `notes/refined/YYYY-MM-DD_HHMMSS.md`: same timestamp, agent-written, a cleaned cohesive transcript with timestamped paragraphs.
- `notes/summaries/YYYY-MM-DD_HHMMSS.md`: same timestamp, agent-written, structured learning notes.

All folders are created automatically. The whole `notes/` folder is git-ignored.

## Verify

Play any video, run `./start.sh`, press Enter once you have a minute or two of speech, and check the printed transcript path. Open the transcript, then open the WAV in VLC to confirm the text matches what was said.

## Limits

- Recording is held in RAM until you press Enter, about 0.7 GB per hour of audio.
- WASAPI loopback delivers no audio while nothing is playing, so silence is not recorded and transcript timestamps are audio time, not wall-clock time.
- Transcription starts only after recording ends; there is no live output during the call.
- Intel Arc / integrated GPUs are not used; CTranslate2 only accelerates on CPU or NVIDIA CUDA.
- Surround output devices are downmixed with a flat average.
- Your own microphone is not captured, only system output.
