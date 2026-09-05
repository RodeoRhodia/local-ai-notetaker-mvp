# AGENTS.md

## Trigger

Any of these requests, and variations of them, mean "run the procedure below":

- "run the transcription program"
- "run the local ai notetaker"
- "start the notetaker"
- "refine the transcript"
- "process the latest transcript"
- "make notes from the recording"

This file applies to any LLM coding agent with a shell and file tools (Claude Code, Codex,
and others). The recording half of the pipeline belongs to the user; your job is the
refinement half: wait for a transcript, do two writing passes, and stop.

## What this repo is

A local notetaker for Windows 11 + WSL2. `./start.sh` calls Windows `python.exe`, records
system audio (a Zoom or Google Meet call, a video, anything on the speakers) until the user
presses Enter, then transcribes it on the CPU with faster-whisper into a timestamped markdown
transcript. Nothing leaves the machine except the one-time model download. The agent stage
turns that raw transcript into a refined transcript and study notes.

| Path | Written by | Content |
| --- | --- | --- |
| `notes/raw/<stem>.wav` | machine | 16 kHz mono 16-bit audio |
| `notes/transcripts/<stem>.md` | machine | raw whisper output: a metadata list, then `[MM:SS - MM:SS] text` lines |
| `notes/refined/<stem>.md` | agent, pass 1 | cleaned readable transcript |
| `notes/summaries/<stem>.md` | agent, pass 2 | learning notes |

The stem is a timestamp like `2026-09-04_132637` and is identical across all four files.
`notes/` is git-ignored.

## Procedure

1. **Tell the user to record.** Ask them to run `./start.sh` in their own WSL terminal, join
   the call or start the audio, and press Enter when they are done. Do not run `start.sh`
   yourself: it needs Windows `python.exe` and an interactive stdin to receive that Enter,
   and transcribing a long call takes minutes (about 2.4x realtime on the reference laptop).
   If the user says the recording already happened, skip to step 2 and run
   `python3 watch.py --any --timeout 60` instead (it returns at once when a transcript exists).
2. **Wait for the transcript.** From the repo root, run:

   ```bash
   python3 watch.py --timeout 540
   ```

   It blocks until a transcript newer than the watcher start exists in `notes/transcripts/`
   with no `notes/refined/<stem>.md` yet, then prints only the absolute path on stdout and
   exits 0. Exit 3 means `Timed out after N s, run again` on stderr: run the same command
   again, and keep going until it prints a path. Exit 130 means Ctrl+C. Flags: `--any` also
   accepts an already existing unrefined transcript (newest first) immediately,
   `--timeout SECONDS`, and `--interval 2` for the poll period. The watcher creates
   `notes/transcripts`, `notes/refined` and `notes/summaries` if they are missing. If your
   shell tool can run a command in the background and notify you when it exits, you may
   instead run `python3 watch.py` with no timeout in the background and wait for it. Never
   poll the folder with your own ad hoc loops; use the watcher.
3. **Read the whole transcript** at the printed path before writing anything. If the body is
   `(no speech detected)`, tell the user and stop.
4. **Pass 1:** write `notes/refined/<stem>.md` following "Refined transcript rules".
5. **Pass 2:** write `notes/summaries/<stem>.md` following "Learning notes template".
6. **Check and report.** Run the "Completeness check", report as described under "Report",
   and stop. One request equals one recording: do not loop back to the watcher for another
   transcript unless the user asks.

## Refined transcript rules

Pass 1 output, `notes/refined/<stem>.md`. Header `# Refined transcript <stem>`, then a
metadata list with three items: `Source: notes/transcripts/<stem>.md` (the transcript, not the
WAV named inside it), `Model:` copied whole from the transcript (for example
`tiny.en (cpu, int8)`), `Audio duration:` as stated in the transcript. Then the body, as prose in paragraphs. Each paragraph begins with the start timestamp of its
first segment in bold, so the text stays navigable against the WAV, for example
`**[03:12]** Full sentences here, in the speaker's own words.` Rules:

- Fix punctuation, capitalisation and obvious speech-to-text errors. Merge fragments into
  complete sentences. Paragraph breaks go where the topic shifts, not at every segment. A
  short recording may be a single paragraph; it still gets its timestamp.
- Remove fillers: um, uh, "you know", repeated words, false starts, stutters.
- Keep every statement, number, name, date, decision, question, example, action item, and
  every joke or aside that carries information.
- Numbers may be written as digits ("15 times 10 is about 150 joules"), but never recompute,
  correct or convert a number, and never fix arithmetic the speaker got wrong.
- Fix the casing of terms and formulas only when context makes them unambiguous
  (`MGH` to `mgh`). Otherwise leave the word as transcribed.
- Never add facts, never summarise, never reorder, never editorialise.
- Unclear passages become `[unclear]`. Do not guess at what was probably said.
- For transcripts longer than 30 minutes of audio, work in order in chunks and never skip a
  chunk. The refined file covers the recording from the first segment to the last.

**Nothing that carries information may be dropped. When in doubt, keep it.**

## Learning notes template

Pass 2 output, `notes/summaries/<stem>.md`, using this skeleton literally:

```markdown
# Notes <stem>

- Refined transcript: [notes/refined/<stem>.md](../refined/<stem>.md) | Audio duration: <as stated>

## Context
What this recording is, and who is speaking if identifiable. 1 to 3 lines.

## Key points
- 5 to 15 bullets covering the most important content.

## Details by topic
### <Topic name>
- Every detail from that topic, not just the highlights.

## Decisions
- What was decided, and by whom if stated.

## Action items
- Who, what, and by when if stated.

## Terms and names
- **<term>**: definition or one-line context. Domain vocabulary counts, not only proper names.

## Open questions
- Questions raised and left unanswered.
```

A section with nothing to put in it says `None mentioned.` on its own line. Bullets are
complete sentences or complete thoughts, never fragments. `## Details by topic` is where
every detail lands, so it is normally the longest section. A recording of a few minutes may
yield fewer than 5 key points; that is fine, the transcript sets the length. These notes are
for studying the material later without replaying the audio, so prefer precise over short.

**Nothing that carries information may be dropped. When in doubt, keep it.**

## Completeness check

Re-read the raw transcript top to bottom. For every fact, number, name, date, decision and
action item in it, confirm it appears in the refined transcript **and** in the notes. Add
anything missing before you report. Only then report to the user. If the check made you add
something, say what in one line above the report block.

## Report

Final message to the user, short, relative paths. The last line must be present verbatim:

```
Transcript: notes/transcripts/<stem>.md
Refined:    notes/refined/<stem>.md
Notes:      notes/summaries/<stem>.md
Audio duration: <as stated in the transcript>
Completeness check: done
```

## Do not

- Commit or push anything under `notes/`.
- Edit `capture.py`, `transcribe.py`, `notetaker.py` or `start.sh`, or run `start.sh` yourself.
- Run pip or install anything, or change the default model (`large-v3-turbo`).
- Delete or move WAVs or transcripts.
- Invent content that is not in the transcript.
- Touch, commit, or comment on unrelated uncommitted changes in the working tree.

## Manual variants

- Transcript already exists: `python3 watch.py --any --timeout 60`, or use the path the user gives you.
- Re-transcribe a WAV: `./start.sh --wav notes/raw/<stem>.wav`. The user runs this, not you.
- Quick self-test for the user: `./start.sh --seconds 20 --model tiny.en` with speech playing.

## Repo conventions

- Python only, standard library where possible, no new dependencies.
- No em dashes in any file. Use commas, colons, or "to" for ranges.
- Small commits, one file per commit where practical, straight to `main`.
- `notes/` and `BENCHMARKS.md` are git-ignored.
