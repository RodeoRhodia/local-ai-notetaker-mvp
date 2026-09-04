# Local AI Notetaker MVP

Records whatever is playing through your Windows speakers and saves it as a 16 kHz mono WAV, ready for local transcription. Nothing leaves your machine.

Current phase: capture only. Transcription is next. See [docs/SPEC.md](docs/SPEC.md).

## Requirements

- Windows 11 with WSL2 (Ubuntu) installed. The repo lives and runs from a WSL shell.
- Windows Python 3.11+ on the Windows side, callable from WSL as `python.exe` (Microsoft Store Python works).
- An enabled audio output device (speakers or headphones).
- VLC or any audio player, to check the recording.

WSL itself has no audio devices. The script always runs with Windows Python; WSL is just where you type the commands.

## Install

From a WSL shell:

```bash
git clone https://github.com/RodeoRhodia/local-ai-notetaker-mvp.git
cd local-ai-notetaker-mvp
(cd /mnt/c && python.exe -m pip install --user -r "$(wslpath -w "$PWD")/requirements.txt")
```

## Run

```bash
./start.sh
```

Records 30 seconds of system audio, then exits. Pass a duration to change it:

```bash
./start.sh 60
```

Ctrl+C stops early and still writes the file.

## Output

`notes/raw/YYYY-MM-DD_HHMM.wav`, 16 kHz, mono, 16-bit PCM. The `notes/` folder is git-ignored.

## Verify

Play any video, run `./start.sh`, then open the WAV in VLC. Speech should sound normal (correct pitch and speed). The console prints an RMS level; if it says SILENT, nothing was playing on the default output device.
