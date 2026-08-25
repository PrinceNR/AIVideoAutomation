from dataclasses import dataclass, replace
from pathlib import Path

from presentation.automation.powerpoint_controller import (
    PowerPointController
)
from presentation.embedders.video_embedder import (
    VideoEmbedder
)
from presentation.com_visual_slot_locator import (
    ComVisualSlotLocator
)
from presentation.presentation_logger import (
    presentation_logger as log,
)
from presentation.video_compatibility import (
    PresentationVideoError,
    SilentVideoNormalizer,
)
from presentation.timeline.parallel_media_timeline import (
    ParallelMediaTimeline,
    ParallelMediaTimelineError,
)


@dataclass(frozen=True)
class SavedVideoPlaybackTarget:
    shape_name: str
    shape_id: int
    slide_advance_time: float
    narration_effects: tuple = ()


@dataclass(frozen=True)
class SavedNarrationEffect:
    shape_name: str
    shape_id: int
    trigger_type: int
    trigger_delay: float
    duration: float


class VideoPresentationProcessor:

    MEDIA_PLAY_EFFECT = 83
    WITH_PREVIOUS = 2

    def __init__(
        self,
        video_normalizer=None,
        controller_factory=None,
    ):
        self.video_embedder = VideoEmbedder()
        self.locator = ComVisualSlotLocator()
        self.video_normalizer = (
            video_normalizer or SilentVideoNormalizer()
        )
        self.controller_factory = (
            controller_factory or PowerPointController
        )
        self.saved_video_targets = {}

    def process(
        self,
        pptx_path,
        lesson,
        template_definition
    ):
        pptx_path = Path(pptx_path).resolve()

        log.detail("=" * 70)
        log.detail("COM VIDEO EMBEDDING")
        log.detail("=" * 70)

        embedded_video_count = 0
        self.saved_video_targets = {}

        with self.controller_factory(visible=True) as ppt:

            ppt.open_presentation(
                pptx_path
            )

            presentation = ppt.presentation
            slide_index = 1

            for word in lesson.words:

                log.detail(f"\nWord: {word.word}")

                for slide_definition in template_definition.slides:

                    slide = presentation.Slides(
                        slide_index
                    )

                    if self._should_embed_video(
                        word,
                        slide_definition
                    ):
                        was_embedded = self._replace_picture_with_video(
                            slide=slide,
                            word=word,
                            slide_index=slide_index,
                            slide_type=slide_definition.type
                        )

                        if was_embedded:
                            embedded_video_count += 1

                    slide_index += 1

            ppt.save()

        if self.saved_video_targets:
            self.verify_saved_video_playback(pptx_path)

        log.detail("\nCOM video embedding completed.")

        return embedded_video_count

    def _should_embed_video(
        self,
        word,
        slide_definition
    ):
        if getattr(
            word,
            "media_type",
            None
        ) != "video":
            return False

        if not getattr(
            word,
            "default_video",
            None
        ):
            return False

        if (
            "image"
            not in slide_definition.processors
        ):
            return False

        return True

    def _replace_picture_with_video(
        self,
        slide,
        word,
        slide_index,
        slide_type
    ):
        picture = self.locator.find_picture(
            slide
        )

        if picture is None:
            log.warning(
                f"  Slide {slide_index} "
                f"({slide_type}): "
                f"no image placeholder found."
            )
            return False

        left = picture.Left
        top = picture.Top
        width = picture.Width
        height = picture.Height
        semantic_name = picture.Name
        slide_advance_time = float(
            slide.SlideShowTransition.AdvanceTime
        )
        original_narration_effects = self._narration_effects(slide)
        silent_video_path = self.video_normalizer.prepare(
            word.default_video
        )

        original_z_order = (
            picture.ZOrderPosition
        )

        picture.Delete()

        media_shape = self.video_embedder.embed(
            slide=slide,
            video_path=silent_video_path,
            left=left,
            top=top,
            width=width,
            height=height
        )
        media_shape.Name = semantic_name
        narration_effects = self._narration_effects(
            slide,
            excluded_shape_id=int(media_shape.Id),
        )

        if not self._narration_schedule_is_preserved(
            original_narration_effects,
            narration_effects,
        ):
            raise PresentationVideoError(
                "Parallel visual-media setup changed the existing "
                "narration schedule."
            )

        self.saved_video_targets[
            slide_index
        ] = SavedVideoPlaybackTarget(
            shape_name=str(semantic_name),
            shape_id=int(media_shape.Id),
            slide_advance_time=slide_advance_time,
            narration_effects=narration_effects,
        )

        self._restore_z_order(
            media_shape,
            original_z_order
        )

        log.detail(
            f"  Slide {slide_index} "
            f"({slide_type}): "
            f"embedded silent autoplay video -> "
            f"{silent_video_path}"
        )

        return True

    def verify_saved_video_playback(
        self,
        pptx_path,
        verify_teaching_timeline=True,
    ):
        with self.controller_factory(visible=True) as ppt:
            ppt.open_presentation(pptx_path)

            for slide_index, target in sorted(
                self.saved_video_targets.items()
            ):
                slide = ppt.presentation.Slides(slide_index)
                media_shape = self.locator.find_picture(slide)

                if (
                    media_shape is None
                    or str(media_shape.Name) != target.shape_name
                    or int(media_shape.Id) != target.shape_id
                ):
                    raise PresentationVideoError(
                        "Saved PowerPoint video target changed on "
                        f"slide {slide_index}."
                    )

                play_settings = (
                    media_shape.AnimationSettings.PlaySettings
                )
                sequence = slide.TimeLine.MainSequence
                playback_effects = []

                for effect_index in range(
                    1,
                    sequence.Count + 1,
                ):
                    effect = sequence.Item(effect_index)

                    try:
                        is_video_playback = (
                            int(effect.EffectType)
                            == self.MEDIA_PLAY_EFFECT
                            and int(effect.Shape.Id)
                            == target.shape_id
                        )
                    except Exception:
                        is_video_playback = False

                    if is_video_playback:
                        playback_effects.append(
                            (effect_index, effect)
                        )

                playback_is_valid = (
                    len(playback_effects) == 1
                    and playback_effects[0][0] == 1
                    and int(
                        playback_effects[0][1]
                        .Timing.TriggerType
                    ) == self.WITH_PREVIOUS
                    and abs(
                        float(
                            playback_effects[0][1]
                            .Timing.TriggerDelayTime
                        )
                    ) < 0.001
                )
                try:
                    parallel_timeline_is_valid = (
                        ParallelMediaTimeline.is_parallel(
                            sequence,
                            media_shape_id=target.shape_id,
                        )
                    )
                except ParallelMediaTimelineError:
                    parallel_timeline_is_valid = False
                media_is_safe = (
                    bool(play_settings.PlayOnEntry)
                    and bool(play_settings.LoopUntilStopped)
                    and not bool(play_settings.PauseAnimation)
                    and not bool(play_settings.HideWhileNotPlaying)
                    and bool(play_settings.RewindMovie)
                    and bool(media_shape.MediaFormat.Muted)
                    and abs(
                        float(media_shape.MediaFormat.Volume)
                    ) < 0.001
                )
                slide_time_is_unchanged = abs(
                    float(
                        slide.SlideShowTransition.AdvanceTime
                    )
                    - target.slide_advance_time
                ) < 0.001
                narration_is_unchanged = (
                    self._narration_effects(
                        slide,
                        excluded_shape_id=target.shape_id,
                    )
                    == target.narration_effects
                )

                if not (
                    playback_is_valid
                    and parallel_timeline_is_valid
                    and media_is_safe
                    and (
                        not verify_teaching_timeline
                        or (
                            slide_time_is_unchanged
                            and narration_is_unchanged
                        )
                    )
                ):
                    raise PresentationVideoError(
                        "Saved PowerPoint visual media is not a "
                        "silent autoplay loop independent of the "
                        f"teaching timeline on slide {slide_index}."
                    )

                log.detail(
                    f"  Slide {slide_index}: verified silent "
                    "autoplay looping visual media."
                )

    @classmethod
    def _narration_effects(
        cls,
        slide,
        excluded_shape_id=None,
    ):
        sequence = slide.TimeLine.MainSequence
        effects = []

        for effect_index in range(1, sequence.Count + 1):
            effect = sequence.Item(effect_index)

            try:
                if int(effect.EffectType) != cls.MEDIA_PLAY_EFFECT:
                    continue

                shape_id = int(effect.Shape.Id)

                if (
                    excluded_shape_id is not None
                    and shape_id == int(excluded_shape_id)
                ):
                    continue

                effects.append(
                    SavedNarrationEffect(
                        shape_name=str(effect.Shape.Name),
                        shape_id=shape_id,
                        trigger_type=int(
                            effect.Timing.TriggerType
                        ),
                        trigger_delay=round(
                            float(
                                effect.Timing.TriggerDelayTime
                            ),
                            3,
                        ),
                        duration=round(
                            float(effect.Timing.Duration),
                            3,
                        ),
                    )
                )
            except Exception as error:
                raise PresentationVideoError(
                    "PowerPoint narration timing could not be "
                    "captured safely before video embedding."
                ) from error

        return tuple(effects)

    @classmethod
    def _narration_schedule_is_preserved(
        cls,
        original_effects,
        parallel_effects,
    ):
        if len(original_effects) != len(parallel_effects):
            return False

        if not original_effects:
            return True

        expected = (
            replace(
                original_effects[0],
                trigger_type=cls.WITH_PREVIOUS,
            ),
            *original_effects[1:],
        )
        return tuple(parallel_effects) == expected

    @staticmethod
    def _restore_z_order(
        shape,
        target_position
    ):

        # PowerPoint adds new shapes at the front.
        # Move the video backward until it reaches
        # the same layer as the original picture.

        while (
            shape.ZOrderPosition
            > target_position
        ):

            shape.ZOrder(3)
