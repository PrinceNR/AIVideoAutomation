from pathlib import Path

from presentation.video_compatibility import (
    PresentationVideoError,
)
from presentation.timeline.parallel_media_timeline import (
    ParallelMediaTimeline,
    ParallelMediaTimelineError,
)


class VideoEmbedder:

    MEDIA_PLAY_EFFECT = 83
    WITH_PREVIOUS = 2
    MSO_TRUE = -1
    MSO_FALSE = 0

    def embed(
        self,
        slide,
        video_path,
        left,
        top,
        width,
        height
    ):
        video_path = str(
            Path(video_path).resolve()
        )

        media_shape = slide.Shapes.AddMediaObject2(
            video_path,
            False,   # LinkToFile
            True,    # SaveWithDocument
            left,
            top,
            width,
            height
        )

        media_shape.LockAspectRatio = False

        media_shape.Left = left
        media_shape.Top = top
        media_shape.Width = width
        media_shape.Height = height

        media_shape.MediaFormat.Muted = self.MSO_TRUE
        media_shape.MediaFormat.Volume = 0.0

        sequence = slide.TimeLine.MainSequence
        playback_effect = sequence.AddEffect(
            media_shape,
            self.MEDIA_PLAY_EFFECT,
        )
        playback_effect.Timing.TriggerType = self.WITH_PREVIOUS
        playback_effect.Timing.TriggerDelayTime = 0.0
        playback_effect.Timing.Duration = 0.001

        try:
            play_settings = (
                playback_effect.EffectInformation.PlaySettings
            )
            play_settings.PlayOnEntry = self.MSO_TRUE
            play_settings.PauseAnimation = self.MSO_FALSE
            play_settings.LoopUntilStopped = self.MSO_TRUE
            play_settings.HideWhileNotPlaying = self.MSO_FALSE
            play_settings.RewindMovie = self.MSO_TRUE
        except Exception as error:
            raise PresentationVideoError(
                "PowerPoint could not configure automatic visual "
                "media playback."
            ) from error

        playback_effect.MoveTo(1)

        try:
            ParallelMediaTimeline.apply(
                sequence,
                media_shape_id=int(media_shape.Id),
            )
        except ParallelMediaTimelineError as error:
            raise PresentationVideoError(
                str(error)
            ) from error

        return media_shape

    def _playback_effect(self, sequence, media_shape):
        matches = []

        for effect_index in range(1, sequence.Count + 1):
            effect = sequence.Item(effect_index)

            try:
                is_match = (
                    int(effect.EffectType)
                    == self.MEDIA_PLAY_EFFECT
                    and int(effect.Shape.Id)
                    == int(media_shape.Id)
                )
            except Exception:
                is_match = False

            if is_match:
                matches.append(effect)

        if len(matches) != 1:
            raise PresentationVideoError(
                "PowerPoint did not create exactly one playback "
                f"effect for visual media '{media_shape.Name}'."
            )

        return matches[0]
