# Vocabulary Video AI

Vocabulary Video AI is a Windows-first Python pipeline that turns a topic and
word count into a complete English-vocabulary lesson: verified content,
selected visual media, pronunciation and narration, an animated PowerPoint,
an MP4, a thumbnail, YouTube metadata, and an optional private upload.

The workflow is resumable. Each stage writes durable artifacts below
`output/<topic>/`, and most standalone stages use the newest lesson when no
explicit path is supplied.

## Current status

Stages 1-6 are operational on Windows with desktop Microsoft PowerPoint. The
current known-good presentation baseline provides configurable animations,
dynamic progress bars, a Fade-by-letter sentence with a moving handwriting
pen, and silent GIF/MP4 autoplay in parallel with teaching text and narration.
The visual clip does not block the teaching sequence or determine slide length.

The handwriting effect is an accepted improved baseline, not pixel-perfect
synchronization. See [Known issues](#known-issues).

## Architecture

```text
main.py
  Stage 1  VocabularyPipeline
           content -> verification -> media planning/selection -> audio
  Stage 2  PresentationPipeline
           template -> slides -> media/audio -> animation/timing patches
  Stage 3  VideoPipeline (PowerPoint -> MP4)
  Stage 4  ThumbnailPipeline (lesson media -> PPTX -> PNG)
  Stage 5  YouTubeMetadataPipeline (lesson -> metadata.json)
  Stage 6  YouTubeUploadPipeline (confirmed private upload)
```

Python builds the presentation, Windows PowerPoint automation applies effects
and exports it, and targeted PresentationML patchers enforce details that the
PowerPoint object model does not reliably persist, such as exact by-letter
timing.

## Repository structure

```text
ai/                  Gemini content, verification, and metadata clients
audio_engine/        TTS, pronunciation, validation, retry, and cleanup
image_engine/        Image search, download, verification, and fallback
media_engine/        Media planning, selection, recovery, and status
models/              Lesson/word models and JSON mapping
pipeline/            Stage 1-6 orchestration
presentation/        PPTX building, animation, timing, embedding, export
templates/           Vocabulary and thumbnail PowerPoint templates
thumbnail_engine/    Thumbnail PPTX generation and PNG export
utils/               File, lesson, logging, and response utilities
verification/        Rule-based and semantic lesson verification
video_engine/        Video search, filtering, verification, and download
youtube_engine/      OAuth and YouTube upload
tests/               Unit, integration, and PowerPoint-focused tests
output/              Generated lessons (ignored by Git)
credentials/         YouTube OAuth files (ignored by Git)
```

## Prerequisites and setup

- Windows with licensed desktop Microsoft PowerPoint.
- Python 3.10 or newer.
- FFmpeg on `PATH` for media conversion/export workflows.
- Accounts/keys for the services enabled in `config.py`.
- A Google OAuth desktop client only for Stage 6.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The dependency lock is a starting point; it does not yet list every imported
PowerPoint, Azure Speech, imaging, test, and YouTube package. Reconciliation is
on the roadmap.

Create `.env` in the repository root and never commit it. Variable names used
by the code (names only) are:

```text
GEMINI_API_KEY
DEEPSEEK_API_KEY
OPENROUTER_API_KEY
AZURE_SPEECH_KEY
AZURE_SPEECH_REGION
ELEVENLABS_API_KEY
PEXELS_API_KEY
PIXABAY_API_KEY
```

For YouTube, put the OAuth desktop-client file at the configured
`YOUTUBE_CLIENT_SECRET_PATH` (currently
`credentials/youtube_client_secret.json`). The refresh token is stored at
`YOUTUBE_TOKEN_PATH`. Both are ignored by Git.

Models, thresholds, voices, templates, animation timing, and YouTube defaults
are centralized in `config.py`.

## Commands and stage behavior

Run the full interactive pipeline:

```powershell
python main.py
```

It asks for topic, word count, and suggestions, runs Stages 1-5, shows the
video/thumbnail/title, and asks before Stage 6. Answering no keeps all generated
artifacts and uploads nothing.

Run stages independently:

```powershell
python -m pipeline.vocabulary_pipeline
python -m pipeline.presentation_pipeline
python -m pipeline.video_pipeline
python -m pipeline.thumbnail_pipeline
python -m pipeline.youtube_metadata_pipeline
python -m pipeline.youtube_upload_pipeline
```

Standalone Stages 2-6 select the most recently modified
`output/*/lesson.json` if no path is passed. Review the printed path when
multiple lessons exist.

### Stage 1 - lesson, media, and audio

Creates or resumes `output/<topic>/lesson.json`. It generates content, performs
rule and semantic verification, applies corrected content when available,
plans `photo`, `illustration`, or `video` per word, builds search queries,
selects/verifies media, and generates audio. It saves after every media and
audio item. The final readiness report records missing/invalid assets.

### Stage 2 - presentation

Loads the lesson, duplicates template slide groups, fills semantic
placeholders, embeds media/audio, adds progress and animations, calculates slide
end times, and writes:

```text
output/<topic>/presentation/<topic>.pptx
```

Narration and teaching effects—not visual-video duration—control slide timing.
Set `PRESENTATION_VERBOSE_LOGGING` in `config.py` for detailed processing logs.

### Stage 3 - video

Uses desktop PowerPoint to export:

```text
output/<topic>/video/<topic>.mp4
```

PowerPoint must remain available in the interactive Windows session while it
renders.

### Stage 4 - thumbnail

Honors each word's `default_image`, fills the thumbnail template, and exports a
1280x720 PNG plus its intermediate PPTX below
`output/<topic>/thumbnail/`.

### Stage 5 - metadata

Generates and validates title, description, tags, and hashtags; trims titles to
100 characters; and writes `output/<topic>/youtube/metadata.json`. A configured
fallback Gemini model handles primary-model unavailability. Temporary service
failure is reported so Stage 5 can be rerun without rebuilding earlier stages.

### Stage 6 - upload

The full workflow requires explicit confirmation. Current defaults are private,
education category, not made for kids, and no subscriber notification. OAuth is
refreshed when possible; an invalid/revoked grant restarts authorization. The
result is saved as `output/<topic>/youtube/upload_result.json`.

Always review `config.py`, MP4, thumbnail, and metadata before confirming.

## Typical output

```text
output/<topic>/
  lesson.json
  audio/<word>/
  images/ and/or downloaded word media
  videos/<word>/
  presentation/<topic>.pptx
  video/<topic>.mp4
  thumbnail/<topic>_thumbnail.pptx
  thumbnail/<topic>_thumbnail.png
  youtube/metadata.json
  youtube/upload_result.json        # only after upload
```

Candidate filenames vary by provider. `lesson.json` is the durable manifest
used by later stages.

## Media/image/GIF/MP4 rules

- The planner selects photo, illustration, or short video for each word.
- Candidates are downloaded, checked, scored, and recovered through fallbacks.
- `word.default_image` is the selected still; `word.default_video` is selected
  motion media. Video also retains a preview still for still-image consumers.
- Compatibility conversion handles unsupported still formats such as manual
  WEBP files.
- GIF/MP4 motion media is normalized to a PowerPoint-compatible silent video.
- Motion media starts automatically at slide entry, stays muted, and remains
  outside the sequential teaching chain.
- Video, narration, and text can run simultaneously. The clip's duration must
  never delay teaching effects or determine slide advancement.

### Manual media workflow (current support)

There is no dedicated override UI/command; the current workflow is manifest
driven:

1. Run Stage 1 once to create the lesson and `lesson.json`.
2. Copy a replacement image, GIF, or MP4 into the lesson folder, preferably in
   a clearly named manual subfolder.
3. Update the word's `default_image` or `default_video` in `lesson.json`; keep
   `preferred_media` consistent with the route.
4. For video, retain a valid `default_image` preview when thumbnails/stills need
   one.
5. Rerun Stage 2 and Stage 3; rerun Stage 4 if the thumbnail should change.

Relative lesson paths and supported absolute paths are accepted. Back up
`lesson.json`: Stage 1 may rewrite fields it assesses as invalid/incomplete.

## Azure TTS, retry, and resume

Azure is the current `TTS_PROVIDER`. Pronunciation and narration have separate
voice/rate settings, and pronunciation must meet the configured assessment
score.

- Existing valid audio is reused on resume; invalid audio is regenerated.
- Synthesis uses temporary partial/attempt files and moves them into place only
  after success and validation.
- Connection, WebSocket, unavailable-service, and timeout failures retry up to
  three attempts with increasing backoff.
- Bad credentials, region, voice, argument, and HTTP 400/401/403 failures are
  permanent and surface immediately.
- Windows sharing-lock cleanup retries, and cleanup errors never replace the
  original synthesis error.
- Stage 1 saves after each word, so reruns preserve completed work.

## Progress bars and animations

Animation effects/durations live in `config.py`. Semantic template shape names
let processors target content without relying solely on slide position.
New-word and continuation transitions are configurable. The progress bar is
computed from vocabulary position and stays consistent across each word's slide
group.

The sentence effect uses PowerPoint Fade-by-letter as the master clock. Saved
PresentationML is patched and verified with the configured exact per-letter
interval. A normalized transparent pen PNG follows an estimated text path,
returns across wrapped lines, and hides after reveal. Narration starts after the
configured handwriting/audio gap.

For motion-media slides, the media play effect is immediate, negligible in
duration, and `With Previous`. The first teaching effect is made concurrent
without changing its delay/duration. Slide end time excludes visual-media
length and follows teaching/audio timing.

## Verification

```powershell
python -m pytest -q
python -m pytest tests/test_presentation_media_timing.py -q
python -m pytest tests/test_handwriting_pen_animation.py -q
python -m pytest tests/test_presentation_visual_animations.py -q
python -m pytest tests/test_video_presentation_processor.py -q
```

The parallel-media change previously passed all 14 focused timing tests and a
real PPTX/MP4 validation: motion media started silently while narration/text
followed their normal teaching timeline. For commit `994c931`, all 184 Python
files passed syntax parsing. Pytest could not be rerun in that commit
environment because pytest was unavailable.

## Troubleshooting

### Stage cannot find a lesson

Run Stage 1 or confirm `output/<topic>/lesson.json` exists. A standalone stage
may have selected a newer lesson than the one intended.

### Azure audio fails immediately

Check `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION`, resource region, and configured
voice. Permanent credentials/configuration errors deliberately do not retry.

### A partial MP3 remains locked

Close players/processes holding it and rerun Stage 1. Unique attempt filenames
are used when a deterministic partial cannot be removed; valid audio remains.

### Media APIs return no result or rate-limit

Wait for cooldown, verify the Pexels/Pixabay key, and rerun Stage 1. Valid
selections are reused and failed words continue through configured fallbacks.

### GIF/MP4 plays before narration instead of beside it

Regenerate Stage 2 with the current template/code and export Stage 3 again.
Confirm the media is silent and no manual PowerPoint edit moved its play effect
into the sequential teaching chain.

### PowerPoint export hangs/fails

Use desktop PowerPoint in an interactive Windows session, dismiss dialogs,
close stale presentations, and verify FFmpeg availability before retrying.

### Thumbnail uses the wrong image

Check `default_image` in `lesson.json`. Stage 4 intentionally uses that path,
not simply the first downloaded candidate.

### YouTube login fails

Verify the OAuth client-secret path. Back up credentials before manual changes;
the uploader normally detects invalid grant and restarts authorization.

## Known-good baseline and history

- `v0.1.0` - end-to-end pipeline operational.
- `v0.1.1` - production presentation template/layout baseline.
- `v0.2.0` - dynamic vocabulary progress bar.
- `35d981f` through `af6b269` - continuity/configurable animations, reliable
  sentence reveal, and cleaner presentation logging.
- `994c931` - Azure cleanup/retry hardening, handwriting-pen baseline, and
  silent parallel visual-media timing verified in real PPTX/MP4 output.

Tags are historical milestones; `main` may be ahead of the latest tag.

## Known issues

- The handwriting pen works but does not follow every visible glyph perfectly,
  especially with proportional fonts, spaces, wrapping, and line returns.
- `requirements.txt` does not yet list every runtime/test integration package.
- Presentation build/export depends on Windows desktop PowerPoint.
- Manual media override requires editing `lesson.json`.
- Standalone stages select the newest lesson instead of offering a picker.
- Exploratory verification pipelines and legacy/manual audio tests remain
  intentionally outside the production baseline pending separate review.

## Prioritized roadmap

1. Add a repeatable real PPTX/MP4 smoke test to prevent media-timeline regressions.
2. Reconcile dependencies and add a safe `.env.example` containing names only.
3. Add a validated, non-destructive manual-media override command/UI.
4. Improve handwriting only after measuring saved PowerPoint glyph/line timing;
   keep the text reveal as master clock and preserve the current fallback.
5. Add explicit stage arguments and lesson selection.
6. Expand end-to-end checkpoint reporting and progress bars for slow operations.
7. Separate fast unit, API integration, PowerPoint COM, and real-export tests.
8. Review experimental verification pipelines and old manual audio tests in a
   separate scoped change before integrating or removing them.

## Safety

- Never commit `.env`, OAuth client secrets, tokens, or secret-bearing logs.
- YouTube upload defaults to private during development.
- Keep generated output/research artifacts out of production commits unless a
  test or template explicitly depends on them.
