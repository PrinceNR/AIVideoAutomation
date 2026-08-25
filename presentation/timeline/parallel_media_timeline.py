from dataclasses import dataclass


class ParallelMediaTimelineError(RuntimeError):
    """Raised when visual media cannot safely run beside teaching effects."""


@dataclass(frozen=True)
class ParallelMediaTimelineState:
    media_index: int
    teaching_index: int | None
    teaching_delay: float | None
    teaching_duration: float | None


class ParallelMediaTimeline:
    """Keeps a visual-media effect outside the sequential teaching chain."""

    MEDIA_PLAY_EFFECT = 83
    WITH_PREVIOUS = 2
    AFTER_PREVIOUS = 3
    MEDIA_SHAPE_NAME = "VOCAB_IMAGE"
    MEDIA_EFFECT_DURATION = 0.001

    @classmethod
    def apply(cls, sequence, media_shape_id=None):
        located = cls._locate_media_effect(
            sequence,
            media_shape_id=media_shape_id,
        )

        if located is None:
            return None

        media_index, media_effect = located

        if media_index != 1:
            raise ParallelMediaTimelineError(
                "Visual media must be the first PowerPoint effect."
            )

        media_is_ready = (
            int(media_effect.Timing.TriggerType)
            == cls.WITH_PREVIOUS
            and abs(
                float(media_effect.Timing.TriggerDelayTime)
            ) < 0.001
            and float(media_effect.Timing.Duration)
            <= cls.MEDIA_EFFECT_DURATION + 0.001
        )

        if not media_is_ready:
            raise ParallelMediaTimelineError(
                "Visual media playback is not an immediate, "
                "non-blocking slide-entry effect."
            )

        if sequence.Count < 2:
            return ParallelMediaTimelineState(
                media_index=media_index,
                teaching_index=None,
                teaching_delay=None,
                teaching_duration=None,
            )

        teaching_effect = sequence.Item(2)
        before = cls._timing_snapshot(teaching_effect)
        trigger_type = int(teaching_effect.Timing.TriggerType)

        if trigger_type == cls.AFTER_PREVIOUS:
            teaching_effect.Timing.TriggerType = cls.WITH_PREVIOUS
        elif trigger_type != cls.WITH_PREVIOUS:
            raise ParallelMediaTimelineError(
                "The first teaching effect is not automatic and "
                "cannot safely run beside visual media."
            )

        after = cls._timing_snapshot(teaching_effect)

        if before != after:
            raise ParallelMediaTimelineError(
                "Parallel visual-media setup changed teaching delay "
                "or duration."
            )

        return ParallelMediaTimelineState(
            media_index=media_index,
            teaching_index=2,
            teaching_delay=after[0],
            teaching_duration=after[1],
        )

    @classmethod
    def is_parallel(cls, sequence, media_shape_id=None):
        located = cls._locate_media_effect(
            sequence,
            media_shape_id=media_shape_id,
        )

        if located is None:
            return False

        media_index, media_effect = located
        media_is_independent = (
            media_index == 1
            and int(media_effect.Timing.TriggerType)
            == cls.WITH_PREVIOUS
            and abs(
                float(media_effect.Timing.TriggerDelayTime)
            ) < 0.001
            and float(media_effect.Timing.Duration)
            <= cls.MEDIA_EFFECT_DURATION + 0.001
        )

        if not media_is_independent:
            return False

        if sequence.Count < 2:
            return True

        return (
            int(sequence.Item(2).Timing.TriggerType)
            == cls.WITH_PREVIOUS
        )

    @classmethod
    def _locate_media_effect(cls, sequence, media_shape_id=None):
        matches = []

        for effect_index in range(1, sequence.Count + 1):
            effect = sequence.Item(effect_index)

            try:
                is_media = (
                    int(effect.EffectType)
                    == cls.MEDIA_PLAY_EFFECT
                )
                matches_shape = (
                    int(effect.Shape.Id) == int(media_shape_id)
                    if media_shape_id is not None
                    else str(effect.Shape.Name)
                    == cls.MEDIA_SHAPE_NAME
                )
            except Exception:
                continue

            if is_media and matches_shape:
                matches.append((effect_index, effect))

        if not matches:
            return None

        if len(matches) != 1:
            raise ParallelMediaTimelineError(
                "PowerPoint contains multiple playback effects for "
                "the same visual media shape."
            )

        return matches[0]

    @staticmethod
    def _timing_snapshot(effect):
        return (
            round(float(effect.Timing.TriggerDelayTime), 3),
            round(float(effect.Timing.Duration), 3),
        )
