# TesVi Video Automation — Project Overview

## What this is

TesVi is a Python pipeline that auto-generates "test/quiz" YouTube-style videos.
Given a hardcoded list of multiple-choice questions, it:

1. Synthesizes voiceover audio (intro, per-question silence/timer beds, a bell
   sound) with Google Text-to-Speech (`gTTS`).
2. Stitches that audio together with `ffmpeg` into one narration track.
3. Renders a video with OpenCV: a talking-avatar intro screen followed by a
   timed question screen (question text, multiple-choice options, and a
   countdown timer) for each question, composited over a blank background
   video and an avatar clip.
4. Muxes the rendered video with the narration audio into a final `.mp4`.

The output is a self-paced quiz video: it speaks instructions, then shows each
question on screen with a visible countdown and a bell to mark time's up.

## How it runs (pipeline)

Entry point: [`src/videomanager/videoStream.py`](src/videomanager/videoStream.py)
(run as `main_video_operator()` — the top-level [`main.py`](main.py) is just
unrelated PyCharm boilerplate and is **not** the real entry point).

```
main_video_operator()
  └─ audio_controller()                         (src/audiomanager/AudioStream.py)
       ├─ builds QuestionsList from questionJson (src/datamanager/QuestionModel.py)
       ├─ create_audio_map()                     — builds an ordered map of
       │     audio clip name -> [duration, filepath], made of:
       │       screen_1.mp3, screen_2.mp3 (static TTS intro/instructions)
       │       question_N_<id>_blank_<timer>.mp3 (silence sized to the
       │         question's countdown timer)
       │       ..._bell (bell.mp3 after each question's silence)
       ├─ concat_audios()                        — ffmpeg-concats all clips
       │     into media/audio/dynamic/normal/main_without_music.mp3
       └─ returns screen_time_map (name -> duration) + QuestionsList
  └─ create_video(screen_time_map, QuestionsList)  (src/videomanager/videoStream.py)
       ├─ get_avatar_stock_images()               — loads avatar_1..12 PNGs
       ├─ opens blank_white_video.mp4 (background) and avatar_video_girl.mp4
       ├─ render_video()                          — frame-by-frame OpenCV loop:
       │     walks screen_time_map in order, and for each timeslot:
       │       "screen_*"   -> overlays avatar video + intro/instruction text
       │       "question_*" -> overlays timer image + countdown + question
       │                        text + 4 options (A/B/C/D)
       │     writes frames to media/video/rendered/test1.mp4
       └─ add_audio_to_video()                    — ffmpeg muxes the rendered
             video with main_without_music.mp3 -> test1_music.mp4 (final output)
```

## Module map

| Path | Responsibility |
|---|---|
| [`src/datamanager/QuestionModel.py`](src/datamanager/QuestionModel.py) | `Question` data class + a **hardcoded** `questionJson` list of 3 sample questions. This is the de facto "question bank" — there's no file/DB loader wired up yet ([`parse_data.py`](src/datamanager/parse_data.py) is an empty stub for that). |
| [`src/audiomanager/AudioStream.py`](src/audiomanager/AudioStream.py) | Builds the ordered audio timeline (`screen_time_map`) and drives narration audio concatenation. |
| [`src/audiomanager/AudioText.py`](src/audiomanager/AudioText.py) | The literal spoken script text for the intro/instruction screens (`screen_1`, `screen_2`). |
| [`src/audiomanager/AudioUtils.py`](src/audiomanager/AudioUtils.py) | Low-level audio helpers: get MP3 duration (`mutagen`), generate silent "blank" clips of a given length, concat multiple audio files, and mix narration with background music — all shelling out to `ffmpeg` via `os.system`/`subprocess`. |
| [`src/audiomanager/AssistantUtils.py`](src/audiomanager/AssistantUtils.py) | Wraps `gTTS` to turn text into speech and save an mp3 (a commented-out Google Cloud TTS variant is kept alongside as a swappable alternative). |
| [`src/audiomanager/AssistantConfig.py`](src/audiomanager/AssistantConfig.py) | A single mutable counter (`LENGTH_SPOKEN`) tracking total characters spoken. |
| [`src/audiomanager/AudioConstants.py`](src/audiomanager/AudioConstants.py) | Path constants for audio assets (blank silence bank, static male/female voice lines, bell, dynamic output location) and audio-mix levels. |
| [`src/videomanager/videoStream.py`](src/videomanager/videoStream.py) | Main render loop (see pipeline above) — the actual entry point. |
| [`src/videomanager/videoUtils.py`](src/videomanager/videoUtils.py) | `ffprobe`/`ffmpeg` helpers: get a video's duration, mux final audio onto the rendered video. |
| [`src/videomanager/photoFrameUtils.py`](src/videomanager/photoFrameUtils.py) | Compositing helper — finds the bounding box of non-white content in a source image/frame (avatar, timer) via thresholding + contours, then pastes just that cropped region onto the output frame at a fixed position (avatar vs. timer slot). |
| [`src/videomanager/VideoConstants.py`](src/videomanager/VideoConstants.py) | Path/layout constants: media locations, output resolution (1920×1080 @ 25fps), font files (Raleway/Ubuntu), timer/avatar screen positions and sizes. |
| [`src/videomanager/TextTemplate.py`](src/videomanager/TextTemplate.py) | Empty stub — unused. |
| [`src/constantdata/ConstantText.py`](src/constantdata/ConstantText.py) | Empty stub — unused. |

## Assets (`media/`)

- `media/audio/static/blank/` — 50 pre-baked silent clips (`blank_1.mp3` … `blank_50.mp3`) used as timer padding per question.
- `media/audio/static/female/` — TTS-recorded intro/instruction lines (`screen_1.mp3`, `screen_2.mp3`).
- `media/audio/static/misc/bell.mp3` — end-of-question chime.
- `media/audio/dynamic/normal/main_without_music.mp3` — generated narration track (build output, checked in as a sample).
- `media/fonts/` — Raleway and Ubuntu TTF families, rendered onto frames via OpenCV's FreeType module.
- `media/photos/avatars/` — 12 avatar PNGs; `media/photos/static/` — timer graphic overlays.
- `media/video/avatars/avatar_video_girl.mp4` — looping talking-avatar clip shown during intro screens.
- `media/video/static/blank_white_video.mp4` — blank background plate the whole video is composited onto.
- `media/video/rendered/` — output directory for rendered videos.

## Setup & running

Per [`README`](README) and [`Requirements.txt`](Requirements.txt):

```bash
pip install -r Requirements.txt
```

```bash
brew install ffmpeg   # or your OS's package manager
```

Then run the video pipeline:

```bash
python src/videomanager/videoStream.py
```

A [`Dockerfile`](Dockerfile) is present (Python 3.8 base, installs ffmpeg),
though its `CMD ["python", "ffmpeg"]` is not a working command — it looks
like unfinished/placeholder container tooling.

## Known issues / rough edges

These are worth knowing before extending the project — none were changed as
part of this documentation pass:

- **Hardcoded absolute paths**: `PROJECT_LOCATION` in both
  [`AudioConstants.py`](src/audiomanager/AudioConstants.py) and
  [`VideoConstants.py`](src/videomanager/VideoConstants.py) is hardcoded to
  `/Users/sheetansh.kumar/PycharmProjects/TesVi/`. The project won't run
  as-is on another machine or checkout path without editing these.
- **Non-relative imports**: [`videoStream.py`](src/videomanager/videoStream.py),
  [`videoUtils.py`](src/videomanager/videoUtils.py) and
  [`photoFrameUtils.py`](src/videomanager/photoFrameUtils.py) import sibling
  modules as bare names (`from VideoConstants import *`) rather than package-
  relative imports, so they only work if run with `src/videomanager/` as the
  working directory / on `sys.path` — not as an installed package.
- **Question bank is hardcoded**: there's no file, spreadsheet, or DB loader
  wired up despite `openpyxl`/`beautifulsoup4` being in requirements
  (`parse_data.py` is an empty stub) — only the 3 sample questions in
  [`QuestionModel.py`](src/datamanager/QuestionModel.py) exist today.
- **`main.py` is unrelated boilerplate** — a default PyCharm "Hi, PyCharm"
  script left over from project creation, not the app entry point.
- **`venv/` (~326 MB, ~3,600 files) is committed to git**, and there is no
  `.gitignore` in the repo. This bloats clone size and will conflict across
  machines/OS versions. Recommend adding a `.gitignore` (`venv/`, `__pycache__/`,
  rendered output, `.DS_Store`) and removing `venv/` from version control.
- **`Dockerfile` looks incomplete**: it `COPY requirements.txt` (lowercase)
  but the real file is [`Requirements.txt`](Requirements.txt) (capitalized),
  and its `CMD` runs `python ffmpeg`, which isn't a valid invocation of this
  project.
- **Interactive render window**: `render_video()` calls `cv2.imshow(...)` and
  waits on `cv2.waitKey(1)`, so rendering pops up a live preview window and
  requires a display — it won't run headless (e.g., in Docker/CI) without
  changes.
- **Pinned dependency versions are dated** (e.g. `numpy~=1.20.2`,
  `opencv-python~=4.5.1.48`) and target Python 3.8; expect friction on newer
  Python/OS versions.

## Dependencies

Core stack: `opencv-python` / `opencv-contrib-python` (video compositing,
text rendering via FreeType), `moviepy`, `gTTS` + `google-cloud-texttospeech`
(text-to-speech, the latter unused/commented out), `mutagen` (audio metadata),
`ffmpeg-python` + system `ffmpeg` (audio/video muxing and concatenation),
`numpy`, `openpyxl` / `beautifulsoup4` (present but not currently used by any
wired-up code path), `gif2numpy`.
