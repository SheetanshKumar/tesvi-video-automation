# TesVi — Automated Test/Quiz Video Generator

TesVi automatically generates self-paced, quiz-style YouTube videos from a
list of multiple-choice questions. It synthesizes narration with
text-to-speech, renders each question on screen with a live countdown timer
and a talking-avatar intro, and produces a finished `.mp4` — no manual video
editing required.

For a deep dive into the pipeline, module-by-module code walkthrough, and
known rough edges, see [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md).

## Features

- Text-to-speech narration (Google `gTTS`) for intro/instruction screens
- Per-question countdown timer synced to spoken audio + a bell cue
- Avatar video overlay during intro screens
- Automated `ffmpeg`-based audio concatenation and audio/video muxing
- OpenCV-based frame rendering at 1920×1080, 25fps

## Requirements

- Python 3.8
- [ffmpeg](https://ffmpeg.org/) available on your `PATH`
- Python packages listed in [`Requirements.txt`](Requirements.txt)

## Setup

```bash
pip install -r Requirements.txt
```

```bash
brew install ffmpeg   # macOS; use your OS's package manager otherwise
```

> **Note:** `PROJECT_LOCATION` is currently hardcoded in
> [`src/audiomanager/AudioConstants.py`](src/audiomanager/AudioConstants.py)
> and [`src/videomanager/VideoConstants.py`](src/videomanager/VideoConstants.py).
> Update it to match your local clone path before running.

## Usage

Run the render pipeline from the `videomanager` directory (imports currently
assume this as the working directory):

```bash
cd src/videomanager
python videoStream.py
```

This will:
1. Generate narration audio for the intro/instructions and per-question
   timer segments, concatenated into
   `media/audio/dynamic/normal/main_without_music.mp3`.
2. Render the video (avatar intro + timed question screens) to
   `media/video/rendered/test1.mp4`.
3. Mux the narration audio onto the rendered video, producing
   `media/video/rendered/test1_music.mp4` as the final output.

Questions are currently defined in
[`src/datamanager/QuestionModel.py`](src/datamanager/QuestionModel.py)
(`questionJson`) — edit that list to change what appears in the video.

## Project structure

```
src/
├── audiomanager/    # TTS narration + audio timeline/mixing (ffmpeg, gTTS)
├── datamanager/      # Question model and question bank
├── videomanager/     # OpenCV render loop, video constants, entry point
└── constantdata/     # Reserved for shared text constants (currently unused)
media/
├── audio/            # Static voice lines, silence bank, bell, generated narration
├── video/             # Avatar clip, blank background plate, rendered output
├── photos/            # Avatar stills, timer graphics
└── fonts/              # Raleway / Ubuntu font families used for on-screen text
```

## Future scope

- **Dynamic question sourcing** — wire up a real loader (spreadsheet via
  `openpyxl`, or a scraped/parsed source via `beautifulsoup4`, both already
  in requirements but unused) instead of the hardcoded `questionJson` list,
  so videos can be generated from an arbitrary question bank.
- **Config-driven paths** — replace the hardcoded absolute `PROJECT_LOCATION`
  with a relative/env-based path so the project runs on any machine without
  edits.
- **Headless rendering** — remove the `cv2.imshow` live-preview requirement
  so the pipeline can run in CI/Docker without a display.
- **Answer review / results screen** — a closing screen or separate video
  that reveals correct answers, matching the "match the answers in the end"
  instruction already spoken in the intro.
- **Multiple avatars/voices** — the avatar image bank (12 avatars) and
  male/female static audio folders already exist but aren't selectable;
  expose this as a configurable option per video.
- **Background music mixing** — `merge_audio_with_music()` already exists in
  `AudioUtils.py` but isn't called from the main pipeline; wire it in so
  rendered videos can include background music.
- **Working Docker image** — fix the `Dockerfile` (wrong requirements
  filename casing, placeholder `CMD`) so the pipeline can build and run in a
  container.
- **Configurable output** — parameterize resolution, frame rate, and output
  filename instead of the current hardcoded `1920×1080`/`test1.mp4`.
