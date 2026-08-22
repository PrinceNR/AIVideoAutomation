from pathlib import Path
from presentation.presentation_logger import (
    presentation_logger as log,
)


class AudioEmbedder:

    MEDIA_PLAY_EFFECT = 83
    AFTER_PREVIOUS = 3

    def embed(
        self,
        slide,
        audio_path: Path,
        start_time: float = 0.0,
        duration: float = 0.0,
        delay: float = 0.0
    ):

        audio_path = Path(audio_path).resolve()

        if not audio_path.exists():
            raise FileNotFoundError(
                f"Audio file not found: {audio_path}"
            )

        # ---------------------------------------------------------
        # 1. Embed audio into PowerPoint
        # ---------------------------------------------------------

        media = slide.Shapes.AddMediaObject2(
            FileName=str(audio_path),
            LinkToFile=False,
            SaveWithDocument=True,
            Left=0,
            Top=0,
            Width=0,
            Height=0
        )

        log.detail(
            f"Audio embedded: {audio_path.name}"
        )

        log.detail(
            f"  Shape: {media.Name}"
        )

        log.detail(
            f"  Type: {media.Type}"
        )

        log.detail(
            f"  ID: {media.Id}"
        )

        # ---------------------------------------------------------
        # 2. Add audio to PowerPoint animation timeline
        # ---------------------------------------------------------

        sequence = slide.TimeLine.MainSequence

        effect = sequence.AddEffect(
            media,
            self.MEDIA_PLAY_EFFECT
        )

        # Play after previous audio.
        effect.Timing.TriggerType = self.AFTER_PREVIOUS

        # Delay before this audio starts.
        effect.Timing.TriggerDelayTime = delay

        # Audio duration.
        effect.Timing.Duration = duration

        # Make sure media plays when effect starts.
        try:
            effect.EffectInformation.PlaySettings.PlayOnEntry = True
        except Exception:
            pass

        # ---------------------------------------------------------
        # 3. Debug information
        # ---------------------------------------------------------

        actual_start_time = start_time

        log.detail(
            "  Animation effect created"
        )

        log.detail(
            f"  Timeline position: "
            f"{start_time:.2f}s"
        )

        log.detail(
            f"  Actual start time: "
            f"{actual_start_time:.2f}s"
        )

        log.detail(
            f"  Duration: "
            f"{duration:.2f}s"
        )

        log.detail(
            f"  Delay: "
            f"{delay:.2f}s"
        )

        return media
