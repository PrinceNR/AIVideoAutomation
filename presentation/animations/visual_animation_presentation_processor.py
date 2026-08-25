from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from presentation.animations.handwriting_pen_asset import (
    HandwritingPenAssetNormalizer,
)
from presentation.animations.visual_animation_planner import (
    AnimationTemplateError,
    VisualAnimationPlanner,
)
from presentation.automation.powerpoint_controller import (
    PowerPointController,
)
from presentation.patchers.sentence_letter_timing_patcher import (
    SentenceLetterTimingPatcher,
)
from presentation.postprocessor.pptx_repacker import PptxRepacker
from presentation.postprocessor.pptx_unpacker import PptxUnpacker
from presentation.presentation_logger import (
    presentation_logger as log,
)
from presentation.timeline.slide_end_time import (
    SlideEndTimeCalculator,
)
from presentation.timeline.parallel_media_timeline import (
    ParallelMediaTimeline,
    ParallelMediaTimelineError,
)


def _powerpoint_constant(name, fallback):
    """Use generated COM constants when available, with documented fallbacks."""
    try:
        from win32com.client import constants

        return int(getattr(constants, name))
    except (AttributeError, ImportError, TypeError, ValueError):
        return fallback


@dataclass(frozen=True)
class RenderedTextLineBounds:
    left: float
    top: float
    width: float
    height: float
    text: str
    visible_character_count: int

    @property
    def right(self):
        return self.left + self.width


@dataclass(frozen=True)
class HandwritingLineTiming:
    line_index: int
    start_time: float
    visible_character_count: int
    writing_duration: float
    return_duration: float
    end_time: float


@dataclass(frozen=True)
class HandwritingTimingPlan:
    letter_delay: float
    lines: tuple[HandwritingLineTiming, ...]

    @property
    def writing_duration(self):
        return sum(
            line.writing_duration
            for line in self.lines
        )

    @property
    def total_duration(self):
        return (
            self.lines[-1].end_time
            if self.lines
            else 0.0
        )

@dataclass(frozen=True)
class HandwritingMotionSegment:
    kind: str
    line_index: int | None
    by_x: float
    by_y: float
    duration: float


@dataclass(frozen=True)
class AudioAnimationAnchor:
    effect: object
    index: int
    duration: float
    delay: float


@dataclass(frozen=True)
class SavedHandwritingTarget:
    sentence_shape_name: str
    sentence_shape_id: int
    audio_shape_name: str
    audio_shape_id: int
    expects_pen: bool
    timing_plan: HandwritingTimingPlan
    motion_segments: tuple[HandwritingMotionSegment, ...]
    expected_audio_end: float
    expected_slide_end: float


class ComShapeNameLocator:

    GROUP_SHAPE_TYPE = 6

    def find(
        self,
        slide,
        shape_name
    ):
        matches = self.find_all(
            slide,
            shape_name,
        )

        return (
            matches[0]
            if matches
            else None
        )

    def find_all(
        self,
        slide,
        shape_name
    ):
        return self._find_all_in_collection(
            slide.Shapes,
            shape_name,
        )

    def _find_all_in_collection(
        self,
        shapes,
        shape_name
    ):
        matches = []

        for index in range(
            1,
            shapes.Count + 1
        ):
            shape = self._item(
                shapes,
                index
            )

            try:
                if shape.Name == shape_name:
                    matches.append(shape)
            except Exception:
                pass

            try:
                is_group = (
                    shape.Type
                    == self.GROUP_SHAPE_TYPE
                )
            except Exception:
                is_group = False

            if is_group:
                matches.extend(
                    self._find_all_in_collection(
                        shape.GroupItems,
                        shape_name,
                    )
                )

        return matches

    @staticmethod
    def _item(
        collection,
        index
    ):
        try:
            return collection.Item(index)
        except (AttributeError, TypeError):
            return collection(index)


class VisualAnimationPresentationProcessor:

    ANIMATION_LEVEL_NONE = _powerpoint_constant(
        "msoAnimateLevelNone",
        0,
    )
    WITH_PREVIOUS = _powerpoint_constant(
        "msoAnimTriggerWithPrevious",
        2,
    )
    AFTER_PREVIOUS = _powerpoint_constant(
        "msoAnimTriggerAfterPrevious",
        3,
    )
    FADE_EFFECT = _powerpoint_constant(
        "msoAnimEffectFade",
        10,
    )
    TEXT_UNIT_BY_CHARACTER = _powerpoint_constant(
        "msoAnimTextUnitEffectByCharacter",
        1,
    )
    PP_ANIMATE_BY_CHARACTER = _powerpoint_constant(
        "ppAnimateByCharacter",
        2,
    )
    PP_ANIMATE_LEVEL_NONE = _powerpoint_constant(
        "ppAnimateLevelNone",
        0,
    )
    MEDIA_PLAY_EFFECT = 83
    CUSTOM_EFFECT = 0
    MOTION_BEHAVIOR = 1
    RECTANGLE_SHAPE = 1
    BRING_TO_FRONT = 0
    SOLID_FILL = 1
    MSO_FALSE = 0
    MSO_TRUE = -1

    def __init__(
        self,
        planner=None,
        locator=None,
        controller_factory=None,
        asset_normalizer=None,
        letter_timing_patcher=None,
        pptx_unpacker=None,
        pptx_repacker=None,
        debug=False,
    ):
        self.planner = (
            planner
            or VisualAnimationPlanner()
        )
        self.locator = (
            locator
            or ComShapeNameLocator()
        )
        self.controller_factory = (
            controller_factory
            or PowerPointController
        )
        self.asset_normalizer = (
            asset_normalizer
            or HandwritingPenAssetNormalizer()
        )
        self.letter_timing_patcher = (
            letter_timing_patcher
            or SentenceLetterTimingPatcher()
        )
        self.pptx_unpacker = pptx_unpacker or PptxUnpacker()
        self.pptx_repacker = pptx_repacker or PptxRepacker()
        self.debug = debug
        self.handwriting_pen_count = 0
        self.handwriting_fallback_count = 0
        self.letter_timing_targets = {}
        self.pen_timing_targets = set()
        self.saved_handwriting_targets = {}
        self.handwriting_timing_plans = {}
        self.handwriting_motion_plans = {}
        self.handwriting_slide_timings = {}

    def process(
        self,
        pptx_path,
        template_path,
    ):
        pptx_path = Path(pptx_path).resolve()
        template_plans = (
            self.planner.build_template_plan(
                template_path
            )
        )

        if not template_plans:
            log.warning(
                "No template slides were available for "
                "visual animation planning."
            )
            return 0

        log.detail("=" * 70)
        log.detail("COM VISUAL ANIMATIONS")
        log.detail("=" * 70)

        processed_slide_count = 0
        self.handwriting_pen_count = 0
        self.handwriting_fallback_count = 0
        self.letter_timing_targets = {}
        self.pen_timing_targets = set()
        self.saved_handwriting_targets = {}
        self.handwriting_timing_plans = {}
        self.handwriting_motion_plans = {}
        self.handwriting_slide_timings = {}

        with self.controller_factory(
            visible=True
        ) as ppt:
            ppt.open_presentation(
                pptx_path
            )

            presentation = ppt.presentation

            for slide_index in range(
                1,
                presentation.Slides.Count + 1
            ):
                slide = presentation.Slides(
                    slide_index
                )
                specs = template_plans[
                    (slide_index - 1)
                    % len(template_plans)
                ]
                slide_within_word = (
                    self.planner.slide_within_word(
                        slide_index
                    )
                )

                self.process_slide(
                    slide,
                    specs,
                    slide_index,
                    slide_within_word,
                )

                target = self.saved_handwriting_targets.get(
                    slide_index
                )

                if target is not None:
                    self._log_handwriting_debug_snapshot(
                        slide,
                        target.sentence_shape_name,
                        slide_index,
                        "BEFORE SAVE",
                    )

                processed_slide_count += 1

            ppt.save()

        if self.letter_timing_targets:
            self._patch_saved_letter_timing(pptx_path)
            saved_letter_timing = (
                self._verify_saved_letter_timing(pptx_path)
            )
            self._verify_saved_handwriting(
                pptx_path,
                saved_letter_timing,
            )

        log.detail(
            "\nCOM visual animation processing completed."
        )

        self._log_handwriting_summary()

        return processed_slide_count

    def _log_handwriting_summary(self):
        if (
            self.planner.settings.sentence_effect
            != "handwriting_pen"
        ):
            return

        summary = (
            "Handwriting pen... "
            f"{self.handwriting_pen_count} sentences"
        )

        if self.handwriting_fallback_count:
            summary += (
                f", {self.handwriting_fallback_count} "
                "text-only fallbacks"
            )

        log.info(summary)

    def _patch_saved_letter_timing(self, pptx_path):
        with TemporaryDirectory() as temp_folder:
            unpacked = Path(temp_folder) / "pptx"
            self.pptx_unpacker.unpack(
                pptx_path,
                unpacked,
            )
            patched_count = self.letter_timing_patcher.patch(
                unpacked / "ppt" / "slides",
                self.letter_timing_targets,
                self.planner.settings.handwriting_letter_delay,
            )

            if patched_count != len(self.letter_timing_targets):
                raise AnimationTemplateError(
                    "PowerPoint handwriting timing was not applied "
                    "to every semantic sentence slide."
                )

            self.pptx_repacker.repack(
                unpacked,
                pptx_path,
            )

    def _verify_saved_letter_timing(self, pptx_path):
        if (
            set(self.saved_handwriting_targets)
            != set(self.letter_timing_targets)
        ):
            raise AnimationTemplateError(
                "Saved handwriting verification targets are "
                "incomplete."
            )

        expected_shape_ids = {
            slide_index: target.sentence_shape_id
            for slide_index, target in (
                self.saved_handwriting_targets.items()
            )
        }

        with TemporaryDirectory() as temp_folder:
            unpacked = Path(temp_folder) / "pptx"
            self.pptx_unpacker.unpack(
                pptx_path,
                unpacked,
            )
            return self.letter_timing_patcher.verify(
                unpacked / "ppt" / "slides",
                self.letter_timing_targets,
                self.planner.settings.handwriting_letter_delay,
                expected_shape_ids=expected_shape_ids,
            )

    def _verify_saved_handwriting(
        self,
        pptx_path,
        saved_letter_timing,
    ):
        # This PowerPoint installation rejects Application.Visible=False;
        # reuse the project's normal visible COM window for verification.
        with self.controller_factory(visible=True) as ppt:
            ppt.open_presentation(pptx_path)

            for slide_index, target in sorted(
                self.saved_handwriting_targets.items()
            ):
                shape_name = target.sentence_shape_name
                slide = ppt.presentation.Slides(slide_index)
                matches = self.locator.find_all(
                    slide,
                    shape_name,
                )

                if len(matches) != 1:
                    raise AnimationTemplateError(
                        "Saved PowerPoint verification expected "
                        f"one '{shape_name}' shape on slide "
                        f"{slide_index}; found {len(matches)}."
                    )

                sentence_shape = matches[0]
                sentence_shape_id = int(sentence_shape.Id)

                if sentence_shape_id != target.sentence_shape_id:
                    raise AnimationTemplateError(
                        "Saved PowerPoint sentence shape ID changed "
                        f"for '{shape_name}' on slide {slide_index}: "
                        f"expected {target.sentence_shape_id}, found "
                        f"{sentence_shape_id}."
                    )

                xml_state = saved_letter_timing.get(
                    slide_index
                )

                if (
                    xml_state is None
                    or xml_state.shape_id != sentence_shape_id
                ):
                    raise AnimationTemplateError(
                        "Saved PowerPoint XML did not verify the "
                        f"final '{shape_name}' shape ID on slide "
                        f"{slide_index}."
                    )

                self._log_handwriting_debug_snapshot(
                    slide,
                    shape_name,
                    slide_index,
                    "AFTER SAVE",
                )

                settings = sentence_shape.AnimationSettings
                sequence = slide.TimeLine.MainSequence
                fade_effects = []
                audio_effects = []
                pen_motion_effects = []
                pen_shape_name = (
                    f"{shape_name}_HANDWRITING_PEN"
                )

                for effect_index in range(
                    1,
                    sequence.Count + 1,
                ):
                    effect = sequence.Item(effect_index)

                    try:
                        effect_shape_name = str(
                            effect.Shape.Name
                        )
                        effect_shape_id = int(
                            effect.Shape.Id
                        )
                    except Exception:
                        effect_shape_name = ""
                        effect_shape_id = None

                    is_sentence = (
                        effect_shape_name == shape_name
                        and effect_shape_id == sentence_shape_id
                    )

                    if (
                        is_sentence
                        and int(effect.EffectType)
                        == self.FADE_EFFECT
                    ):
                        fade_effects.append(
                            (effect_index, effect)
                        )

                    if (
                        int(effect.EffectType)
                        == self.MEDIA_PLAY_EFFECT
                        and effect_shape_name
                        == target.audio_shape_name
                        and effect_shape_id
                        == target.audio_shape_id
                    ):
                        audio_effects.append(
                            (effect_index, effect)
                        )

                    if (
                        effect_shape_name == pen_shape_name
                        and int(effect.EffectType)
                        == self.CUSTOM_EFFECT
                    ):
                        pen_motion_effects.append(
                            (effect_index, effect)
                        )

                has_valid_legacy_text_settings = (
                    bool(settings.Animate)
                    and int(settings.TextUnitEffect)
                    == self.PP_ANIMATE_BY_CHARACTER
                    and int(settings.TextLevelEffect)
                    != self.PP_ANIMATE_LEVEL_NONE
                )
                reveal_masks = [
                    shape
                    for shape in self.locator.find_all(
                        slide,
                        f"{shape_name}_REVEAL_MASK",
                    )
                ]
                reveal_masks.extend(
                    self._generated_line_masks(
                        slide,
                        shape_name,
                    )
                )
                timeline_is_synchronized = False
                parallel_timeline_is_valid = True
                shared_timing_is_valid = (
                    self._saved_handwriting_timing_is_valid(
                        target,
                        xml_state,
                        pen_motion_effects,
                    )
                )
                saved_slide_end = float(
                    slide.SlideShowTransition.AdvanceTime
                )
                slide_timing_is_valid = (
                    saved_slide_end + 0.001
                    >= target.expected_audio_end
                    and abs(
                        saved_slide_end
                        - target.expected_slide_end
                    ) < 0.001
                )

                if (
                    len(fade_effects) == 1
                    and len(audio_effects) == 1
                ):
                    fade_index, fade_effect = fade_effects[0]
                    audio_index, _audio_effect = audio_effects[0]
                    expects_pen = target.expects_pen
                    try:
                        has_visual_media = (
                            ParallelMediaTimeline._locate_media_effect(
                                sequence
                            )
                            is not None
                        )
                        parallel_timeline_is_valid = (
                            not has_visual_media
                            or ParallelMediaTimeline.is_parallel(
                                sequence
                            )
                        )
                    except ParallelMediaTimelineError:
                        has_visual_media = True
                        parallel_timeline_is_valid = False
                    expected_fade_trigger = (
                        self.WITH_PREVIOUS
                        if has_visual_media
                        else self.AFTER_PREVIOUS
                    )

                    if expects_pen and pen_motion_effects:
                        first_pen_index, first_pen = (
                            pen_motion_effects[0]
                        )
                        timeline_is_synchronized = (
                            fade_index < first_pen_index < audio_index
                            and audio_index == sequence.Count
                            and int(fade_effect.Timing.TriggerType)
                            == expected_fade_trigger
                            and int(first_pen.Timing.TriggerType)
                            == self.WITH_PREVIOUS
                            and abs(
                                float(
                                    fade_effect.Timing.TriggerDelayTime
                                )
                                - float(
                                    first_pen.Timing.TriggerDelayTime
                                )
                            ) < 0.001
                        )
                    elif not expects_pen:
                        timeline_is_synchronized = (
                            fade_index < audio_index
                            and audio_index == sequence.Count
                        )

                if (
                    len(fade_effects) != 1
                    or len(audio_effects) != 1
                    or reveal_masks
                    or not timeline_is_synchronized
                    or not parallel_timeline_is_valid
                    or not shared_timing_is_valid
                    or not slide_timing_is_valid
                ):
                    raise AnimationTemplateError(
                        "Saved PowerPoint slide "
                        f"{slide_index} did not preserve one native "
                        f"Fade-by-letter effect for '{shape_name}' "
                        "without reveal masks."
                    )

                log.detail(
                    f"  Slide {slide_index}: verified "
                    f"{shape_name} Fade-by-letter; "
                    f"XML interval={xml_state.letter_delay_ms}ms, "
                    "shared line timing=verified, "
                    "legacy projection="
                    f"{'character' if has_valid_legacy_text_settings else 'normalized'}."
                )

    @staticmethod
    def _saved_handwriting_timing_is_valid(
        target,
        xml_state,
        pen_motion_effects,
    ):
        letter_delay = xml_state.letter_delay_ms / 1000.0
        total_visible_characters = sum(
            line.visible_character_count
            for line in target.timing_plan.lines
        )
        expected_writing_duration = (
            total_visible_characters * letter_delay
        )
        plan_matches_text = abs(
            target.timing_plan.writing_duration
            - expected_writing_duration
        ) < 0.001
        line_order_is_valid = all(
            abs(
                current.start_time
                - previous.end_time
            ) < 0.001
            for previous, current in zip(
                target.timing_plan.lines,
                target.timing_plan.lines[1:],
            )
        )

        if not target.expects_pen:
            return plan_matches_text and line_order_is_valid

        actual_pen_durations = tuple(
            float(effect.Timing.Duration)
            for _index, effect in pen_motion_effects
        )
        expected_pen_durations = tuple(
            segment.duration
            for segment in target.motion_segments
        )
        pen_matches_plan = (
            len(actual_pen_durations)
            == len(expected_pen_durations)
            and all(
                abs(actual - expected) < 0.001
                for actual, expected in zip(
                    actual_pen_durations,
                    expected_pen_durations,
                )
            )
        )

        return (
            plan_matches_text
            and line_order_is_valid
            and pen_matches_plan
        )

    def _log_handwriting_debug_snapshot(
        self,
        slide,
        shape_name,
        slide_index,
        phase,
    ):
        if not (self.debug or log.verbose):
            return

        matches = self.locator.find_all(
            slide,
            shape_name,
        )

        if len(matches) != 1:
            log.detail(
                f"  [{phase}] Slide {slide_index}: "
                f"{shape_name} matches={len(matches)}."
            )
            return

        shape = matches[0]
        settings = shape.AnimationSettings
        sequence = slide.TimeLine.MainSequence
        text = self._shape_text(shape)

        log.detail(
            f"  [{phase}] Slide {slide_index}: "
            f"name={shape.Name}, ID={shape.Id}, text={text!r}."
        )
        log.detail(
            "    AnimationSettings: "
            f"Animate={self._safe_attribute(settings, 'Animate')}, "
            f"EntryEffect={self._safe_attribute(settings, 'EntryEffect')}, "
            "TextUnitEffect="
            f"{self._safe_attribute(settings, 'TextUnitEffect')}, "
            "TextLevelEffect="
            f"{self._safe_attribute(settings, 'TextLevelEffect')}."
        )
        log.detail(
            f"    MainSequence effects={sequence.Count}."
        )

        for effect_index in range(1, sequence.Count + 1):
            effect = sequence.Item(effect_index)
            effect_shape = self._safe_attribute(
                effect,
                "Shape",
            )
            effect_information = self._safe_attribute(
                effect,
                "EffectInformation",
            )
            effect_parameters = self._safe_attribute(
                effect,
                "EffectParameters",
            )

            log.detail(
                f"    effect[{effect_index}]: "
                "target="
                f"{self._safe_attribute(effect_shape, 'Name')}, "
                f"ID={self._safe_attribute(effect_shape, 'Id')}, "
                f"type={self._safe_attribute(effect, 'EffectType')}, "
                "trigger="
                f"{self._safe_attribute(effect.Timing, 'TriggerType')}, "
                "delay="
                f"{self._safe_attribute(effect.Timing, 'TriggerDelayTime')}, "
                "duration="
                f"{self._safe_attribute(effect.Timing, 'Duration')}, "
                "textUnit="
                f"{self._safe_attribute(effect_information, 'TextUnitEffect')}, "
                "textLevel="
                f"{self._safe_attribute(effect_information, 'TextLevelEffect')}, "
                "direction="
                f"{self._safe_attribute(effect_parameters, 'Direction')}."
            )

    @staticmethod
    def _shape_text(shape):
        getters = (
            lambda: shape.TextFrame2.TextRange.Text,
            lambda: shape.TextFrame.TextRange.Text,
        )

        for getter in getters:
            try:
                return str(getter())
            except Exception:
                continue

        return ""

    @staticmethod
    def _safe_attribute(value, name):
        if value is None:
            return ""

        try:
            return getattr(value, name)
        except Exception:
            return ""

    def _generated_line_masks(self, slide, shape_name):
        prefix = f"{shape_name}_REVEAL_MASK_LINE_"
        matches = []

        for shape_index in range(1, slide.Shapes.Count + 1):
            shape = self.locator._item(
                slide.Shapes,
                shape_index,
            )

            try:
                if str(shape.Name).startswith(prefix):
                    matches.append(shape)
            except Exception:
                pass

        return matches

    def process_slide(
        self,
        slide,
        specs,
        slide_index,
        slide_within_word,
    ):
        self._apply_transition(
            slide,
            slide_index,
            slide_within_word,
        )

        sequence = slide.TimeLine.MainSequence
        expected_audio_shape_name = (
            self._expected_sentence_audio_shape_name(specs)
        )
        audio_anchor = self._automatic_audio_anchor(
            sequence,
            expected_shape_name=expected_audio_shape_name,
        )
        insertion_index = (
            audio_anchor.index + 1
            if audio_anchor is not None
            else None
        )
        anchor_duration = (
            audio_anchor.duration
            if audio_anchor is not None
            else None
        )

        for spec in specs:
            try:
                matches = self.locator.find_all(
                    slide,
                    spec.shape_name,
                )
            except Exception as error:
                if spec.required:
                    raise AnimationTemplateError(
                        "Rendered presentation slide "
                        f"{slide_index} could not locate required "
                        f"semantic shape '{spec.shape_name}': "
                        f"{error}"
                    ) from error

                log.warning(
                    f"  Slide {slide_index}: visual shape "
                    f"lookup for '{spec.shape_name}' "
                    f"failed safely: {error}"
                )
                continue

            if spec.required and len(matches) != 1:
                raise AnimationTemplateError(
                    "Rendered presentation slide "
                    f"{slide_index} must contain exactly one "
                    f"required semantic shape "
                    f"'{spec.shape_name}'; "
                    f"found {len(matches)}."
                )

            if not matches:
                log.warning(
                    f"  Slide {slide_index}: optional visual "
                    f"shape '{spec.shape_name}' "
                    "was not found; animation skipped."
                )
                continue

            if len(matches) > 1:
                log.warning(
                    f"  Slide {slide_index}: optional visual "
                    f"shape name '{spec.shape_name}' matched "
                    f"{len(matches)} shapes; animation skipped."
                )
                continue

            shape = matches[0]

            if spec.reveal_mode == "handwriting_pen":
                pen_applied = (
                    self._append_handwriting_pen_effect(
                        slide,
                        sequence,
                        shape,
                        spec,
                        slide_index,
                        audio_anchor,
                    )
                )
                self.letter_timing_targets[
                    slide_index
                ] = spec.shape_name

                if pen_applied:
                    self.handwriting_pen_count += 1
                    self.pen_timing_targets.add(
                        slide_index
                    )
                else:
                    self.handwriting_fallback_count += 1

                self.saved_handwriting_targets[
                    slide_index
                ] = self._saved_handwriting_target(
                    shape,
                    audio_anchor,
                    pen_applied,
                    spec.shape_name,
                    self.handwriting_timing_plans[
                        slide_index
                    ],
                    self.handwriting_motion_plans[
                        slide_index
                    ],
                    self.handwriting_slide_timings[
                        slide_index
                    ],
                )

            elif spec.reveal_mode == "reveal_mask":
                self._append_reveal_mask_effect(
                    slide,
                    sequence,
                    shape,
                    spec,
                    slide_index,
                    insertion_index,
                    anchor_duration,
                )
            else:
                self._append_effect(
                    sequence,
                    shape,
                    spec,
                    slide_index,
                    insertion_index,
                    anchor_duration,
                )

        try:
            ParallelMediaTimeline.apply(sequence)
        except ParallelMediaTimelineError as error:
            raise AnimationTemplateError(
                "Rendered presentation slide "
                f"{slide_index} could not keep visual media "
                f"independent from the teaching timeline: {error}"
            ) from error

    def _automatic_audio_anchor(
        self,
        sequence,
        expected_shape_name=None,
    ):
        for index in range(
            1,
            sequence.Count + 1
        ):
            try:
                effect = sequence.Item(index)

                if (
                    effect.EffectType
                    != self.MEDIA_PLAY_EFFECT
                ):
                    continue

                try:
                    if str(effect.Shape.Name) == "VOCAB_IMAGE":
                        continue
                except Exception:
                    continue

                if expected_shape_name is not None:
                    try:
                        if (
                            str(effect.Shape.Name)
                            != expected_shape_name
                        ):
                            continue
                    except Exception:
                        continue

                duration = float(
                    effect.Timing.Duration
                )

                if duration > 0:
                    return AudioAnimationAnchor(
                        effect=effect,
                        index=index,
                        duration=duration,
                        delay=float(
                            effect.Timing.TriggerDelayTime
                        ),
                    )

            except Exception:
                continue

        # With no usable audio anchor, AddEffect safely appends.
        return None

    @staticmethod
    def _expected_sentence_audio_shape_name(specs):
        sentence_specs = [
            spec
            for spec in specs
            if spec.required
            and spec.reveal_mode == "handwriting_pen"
            and spec.semantic_element in {
                "past_sentence",
                "present_sentence",
                "future_sentence",
            }
        ]

        if len(sentence_specs) == 1:
            return sentence_specs[0].semantic_element

        return None

    @staticmethod
    def _saved_handwriting_target(
        sentence_shape,
        audio_anchor,
        expects_pen,
        shape_name,
        timing_plan,
        motion_segments,
        slide_timing,
    ):
        if audio_anchor is None:
            raise AnimationTemplateError(
                "Handwriting persistence requires a semantic "
                "narration audio target."
            )

        try:
            audio_shape = audio_anchor.effect.Shape
            return SavedHandwritingTarget(
                sentence_shape_name=shape_name,
                sentence_shape_id=int(sentence_shape.Id),
                audio_shape_name=str(audio_shape.Name),
                audio_shape_id=int(audio_shape.Id),
                expects_pen=bool(expects_pen),
                timing_plan=timing_plan,
                motion_segments=tuple(motion_segments),
                expected_audio_end=float(
                    slide_timing["audio_end"]
                ),
                expected_slide_end=float(
                    slide_timing["slide_end"]
                ),
            )
        except Exception as error:
            raise AnimationTemplateError(
                "PowerPoint handwriting shape identities are "
                "unavailable for saved-file verification."
            ) from error

    def _apply_transition(
        self,
        slide,
        slide_index,
        slide_within_word,
    ):
        transition_spec = (
            self.planner.transition_spec(
                slide_within_word
            )
        )

        try:
            transition = (
                slide.SlideShowTransition
            )
            transition.EntryEffect = (
                transition_spec.entry_effect
            )
            transition.Speed = (
                transition_spec.speed
            )
        except Exception as error:
            log.warning(
                f"  Slide {slide_index}: transition "
                f"could not be applied: {error}"
            )

    def _append_effect(
        self,
        sequence,
        shape,
        spec,
        slide_index,
        insertion_index,
        anchor_duration,
    ):
        effect = None

        try:
            effect = self._add_effect(
                sequence,
                shape,
                spec.effect_id,
                insertion_index,
            )

            if spec.direction is not None:
                effect.EffectParameters.Direction = (
                    spec.direction
                )

            trigger_delay = (
                self.planner.settings.visual_delay
            )
            duration = spec.duration

            if anchor_duration is not None:
                duration = min(
                    duration,
                    anchor_duration,
                )

            effect.Timing.TriggerType = (
                self.WITH_PREVIOUS
            )
            effect.Timing.TriggerDelayTime = trigger_delay
            effect.Timing.Duration = duration

            log.detail(
                f"  Slide {slide_index}: "
                f"{spec.semantic_element} -> "
                f"{spec.shape_name}"
            )

        except Exception as error:
            if effect is not None:
                try:
                    effect.Delete()
                except Exception:
                    pass

            log.warning(
                f"  Slide {slide_index}: visual animation "
                f"for '{spec.shape_name}' failed safely: "
                f"{error}"
            )

    def _append_reveal_mask_effect(
        self,
        slide,
        sequence,
        sentence_shape,
        spec,
        slide_index,
        insertion_index,
        anchor_duration,
    ):
        mask = None
        effect = None

        try:
            if spec.reveal_direction != "left_to_right":
                raise AnimationTemplateError(
                    "Sentence reveal mask supports only the "
                    "configured left-to-right direction."
                )

            mask = self._create_reveal_mask(
                slide,
                sentence_shape,
                spec,
            )
            effect = self._add_effect(
                sequence,
                mask,
                spec.effect_id,
                insertion_index,
            )
            behavior = effect.Behaviors.Add(
                self.MOTION_BEHAVIOR
            )
            slide_width = self._slide_width(slide)
            reveal_distance = (
                self._motion_distance_percent(
                    mask.Width,
                    slide_width,
                )
            )
            behavior.MotionEffect.ByX = reveal_distance
            behavior.MotionEffect.ByY = 0.0

            trigger_delay = (
                self.planner.settings.sentence_delay
            )
            duration = spec.duration

            if anchor_duration is not None:
                duration = min(
                    duration,
                    max(
                        0.0,
                        anchor_duration - trigger_delay,
                    ),
                )

            effect.Timing.TriggerType = (
                self.WITH_PREVIOUS
            )
            effect.Timing.TriggerDelayTime = trigger_delay
            effect.Timing.Duration = duration

            log.detail(
                f"  Slide {slide_index}: "
                f"{spec.shape_name} -> reveal mask "
                f"({duration:.2f}s)."
            )

            return {
                "mask": mask,
                "effect": effect,
                "duration": duration,
            }

        except Exception as error:
            self._delete_effect(effect)
            self._delete_shape(mask)
            raise AnimationTemplateError(
                "Rendered presentation slide "
                f"{slide_index} could not construct a safe "
                f"reveal mask for '{spec.shape_name}': {error}"
            ) from error

    def _append_handwriting_pen_effect(
        self,
        slide,
        sequence,
        sentence_shape,
        spec,
        slide_index,
        audio_anchor,
    ):
        pen_spec = spec.handwriting_pen
        pen_shape = None
        text_effect = None
        pen_effects = []
        fallback_reason = None
        fallback_is_problem = False

        try:
            if audio_anchor is None:
                raise AnimationTemplateError(
                    "Handwriting sentence animation requires its "
                    "embedded narration audio effect."
                )

            if pen_spec is None:
                raise AnimationTemplateError(
                    "Handwriting pen plan is incomplete."
                )

            lines = self._rendered_text_line_bounds(
                sentence_shape
            )
            timing_plan = self._handwriting_line_timing_plan(
                lines,
                pen_spec.letter_delay,
                pen_spec.line_return_duration,
            )
            segments = self._handwriting_motion_segments(
                lines,
                timing_plan,
            )
            self.handwriting_timing_plans[
                slide_index
            ] = timing_plan
            self.handwriting_motion_plans[
                slide_index
            ] = segments
            handwriting_duration = timing_plan.total_duration
            handwriting_start = (
                audio_anchor.delay
                + self.planner.settings.sentence_delay
            )
            text_effect = self._append_sentence_fade_by_letter(
                sequence,
                sentence_shape,
                audio_anchor.index,
                handwriting_start,
                timing_plan,
            )
            fallback_reason, fallback_is_problem = (
                self._handwriting_fallback_reason(pen_spec)
            )

            if fallback_reason is None:
                try:
                    pen_shape = self._create_handwriting_pen(
                        slide,
                        lines[0],
                        spec,
                    )
                except Exception as error:
                    fallback_reason = str(error)
                    fallback_is_problem = True

            if pen_shape is not None:
                try:
                    audio_index = self._sequence_effect_index(
                        sequence,
                        audio_anchor.effect,
                    )
                    hide_duration = self._append_handwriting_timeline(
                        slide,
                        sequence,
                        pen_shape,
                        segments,
                        audio_index,
                        handwriting_start,
                        pen_effects,
                        pen_spec.hide_after_reveal,
                        pen_spec.pen_hide_duration,
                    )
                    handwriting_duration += hide_duration
                except Exception as error:
                    for effect in reversed(pen_effects):
                        self._delete_effect(effect)

                    pen_effects.clear()
                    self._delete_shape(pen_shape)
                    pen_shape = None
                    fallback_reason = (
                        "PowerPoint could not construct the synchronized "
                        f"pen path: {error}"
                    )
                    fallback_is_problem = True

            self._move_audio_after_handwriting(
                sequence,
                audio_anchor.effect,
            )
            timing = self._reschedule_sentence_audio(
                slide,
                audio_anchor,
                handwriting_start,
                handwriting_duration,
                pen_spec.audio_gap,
            )
            self.handwriting_slide_timings[
                slide_index
            ] = timing

            if fallback_reason is not None:
                message = (
                    f"Slide {slide_index}: handwriting pen for "
                    f"'{spec.shape_name}' used native text-only "
                    f"fallback without masks: {fallback_reason}."
                )

                if fallback_is_problem:
                    log.warning(message)
                else:
                    log.detail(message)

            log.detail(
                f"  Slide {slide_index}: "
                f"{spec.shape_name} -> "
                "Fade-by-letter"
                f"{' + handwriting pen' if pen_shape else ''} "
                f"({handwriting_duration:.2f}s, "
                f"{timing_plan.letter_delay:.3f}s/letter, "
                f"{len(lines)} lines); "
                f"audio={timing['audio_start']:.2f}s, "
                f"slide={timing['slide_end']:.2f}s."
            )

            return pen_shape is not None

        except Exception as error:
            for effect in reversed(pen_effects):
                self._delete_effect(effect)

            self._delete_effect(text_effect)
            self._delete_shape(pen_shape)

            raise AnimationTemplateError(
                "Rendered presentation slide "
                f"{slide_index} could not construct synchronized "
                f"handwriting for '{spec.shape_name}': {error}"
            ) from error

    def _append_sentence_fade_by_letter(
        self,
        sequence,
        sentence_shape,
        insertion_index,
        handwriting_start,
        timing_plan,
    ):
        effect = self._add_effect(
            sequence,
            sentence_shape,
            self.FADE_EFFECT,
            insertion_index,
        )

        try:
            converted = sequence.ConvertToTextUnitEffect(
                effect,
                self.TEXT_UNIT_BY_CHARACTER,
            )

            if converted is None:
                raise AnimationTemplateError(
                    "PowerPoint returned no by-character Fade effect."
                )

            effect = converted

            if insertion_index is not None:
                effect.MoveTo(insertion_index)

            effect.Timing.TriggerType = self.AFTER_PREVIOUS
            effect.Timing.TriggerDelayTime = handwriting_start
            effect.Timing.Duration = float(
                timing_plan.letter_delay
            )

            if int(effect.EffectType) != self.FADE_EFFECT:
                raise AnimationTemplateError(
                    "PowerPoint did not retain the native Fade effect."
                )

            if (
                int(effect.EffectInformation.TextUnitEffect)
                != self.TEXT_UNIT_BY_CHARACTER
            ):
                raise AnimationTemplateError(
                    "PowerPoint did not retain by-character text units."
                )

            return effect

        except Exception:
            self._delete_effect(effect)
            raise

    @staticmethod
    def _move_audio_after_handwriting(
        sequence,
        audio_effect,
    ):
        try:
            audio_effect.MoveTo(sequence.Count)
        except Exception as error:
            raise AnimationTemplateError(
                "PowerPoint could not place sentence narration "
                "after the handwriting effects."
            ) from error

    def _sequence_effect_index(self, sequence, target_effect):
        for effect_index in range(1, sequence.Count + 1):
            effect = sequence.Item(effect_index)

            if effect is target_effect:
                return effect_index

            try:
                if effect._oleobj_ == target_effect._oleobj_:
                    return effect_index
            except Exception:
                pass

        try:
            target_shape_name = str(target_effect.Shape.Name)
            target_duration = float(target_effect.Timing.Duration)
            target_delay = float(
                target_effect.Timing.TriggerDelayTime
            )
        except Exception as error:
            raise AnimationTemplateError(
                "PowerPoint sentence audio metadata became unavailable."
            ) from error

        candidates = []

        for effect_index in range(1, sequence.Count + 1):
            effect = sequence.Item(effect_index)

            try:
                is_match = (
                    int(effect.EffectType) == self.MEDIA_PLAY_EFFECT
                    and str(effect.Shape.Name) == target_shape_name
                    and abs(
                        float(effect.Timing.Duration)
                        - target_duration
                    ) < 0.001
                    and abs(
                        float(effect.Timing.TriggerDelayTime)
                        - target_delay
                    ) < 0.001
                )
            except Exception:
                is_match = False

            if is_match:
                candidates.append(effect_index)

        if len(candidates) == 1:
            return candidates[0]

        raise AnimationTemplateError(
            "PowerPoint sentence audio effect disappeared from "
            "the animation sequence."
        )

    def _append_handwriting_timeline(
        self,
        slide,
        sequence,
        pen_shape,
        segments,
        insertion_index,
        handwriting_start,
        created_effects,
        hide_after_reveal,
        hide_duration,
    ):
        slide_width = self._slide_width(slide)
        slide_height = self._slide_height(slide)
        next_effect_index = insertion_index
        first_write = True

        for segment in segments:
            pen_effect = self._add_effect(
                sequence,
                pen_shape,
                self.CUSTOM_EFFECT,
                next_effect_index,
            )
            created_effects.append(pen_effect)
            next_effect_index += 1
            self._configure_motion_effect(
                pen_effect,
                segment,
                slide_width,
                slide_height,
                (
                    self.WITH_PREVIOUS
                    if first_write
                    else self.AFTER_PREVIOUS
                ),
                (
                    handwriting_start
                    if first_write
                    else 0.0
                ),
            )

            first_write = False

        if not hide_after_reveal:
            return 0.0

        hide_effect = self._add_effect(
            sequence,
            pen_shape,
            self.FADE_EFFECT,
            next_effect_index,
        )
        created_effects.append(hide_effect)
        hide_effect.Exit = self.MSO_TRUE
        hide_effect.Timing.TriggerType = self.AFTER_PREVIOUS
        hide_effect.Timing.TriggerDelayTime = 0.0
        hide_effect.Timing.Duration = float(hide_duration)
        return float(hide_duration)

    def _configure_motion_effect(
        self,
        effect,
        segment,
        slide_width,
        slide_height,
        trigger_type,
        trigger_delay,
    ):
        behavior = effect.Behaviors.Add(
            self.MOTION_BEHAVIOR
        )
        behavior.MotionEffect.ByX = (
            self._motion_distance_percent(
                segment.by_x,
                slide_width,
                allow_negative=True,
                allow_zero=True,
            )
        )
        behavior.MotionEffect.ByY = (
            self._motion_distance_percent(
                segment.by_y,
                slide_height,
                allow_negative=True,
                allow_zero=True,
            )
        )
        effect.Timing.TriggerType = trigger_type
        effect.Timing.TriggerDelayTime = trigger_delay
        effect.Timing.Duration = segment.duration

    def _reschedule_sentence_audio(
        self,
        slide,
        audio_anchor,
        handwriting_start,
        handwriting_duration,
        audio_gap,
    ):
        transition = slide.SlideShowTransition
        original_slide_end = float(transition.AdvanceTime)
        original_audio_end = (
            audio_anchor.delay + audio_anchor.duration
        )
        end_padding = max(
            0.0,
            original_slide_end - original_audio_end,
        )
        audio_start = (
            handwriting_start
            + handwriting_duration
            + float(audio_gap)
        )
        audio_end = audio_start + audio_anchor.duration
        handwriting_end = (
            handwriting_start + handwriting_duration
        )
        original_required_end = max(
            0.0,
            original_slide_end - end_padding,
        )
        slide_end = SlideEndTimeCalculator.calculate(
            latest_audio_end=audio_end,
            latest_handwriting_end=handwriting_end,
            latest_visual_end=original_required_end,
            end_padding=end_padding,
        )

        audio_anchor.effect.Timing.TriggerType = (
            self.AFTER_PREVIOUS
        )
        audio_anchor.effect.Timing.TriggerDelayTime = float(
            audio_gap
        )
        transition.AdvanceOnTime = True
        transition.AdvanceTime = slide_end

        return {
            "audio_start": audio_start,
            "audio_end": audio_end,
            "handwriting_end": handwriting_end,
            "slide_end": slide_end,
            "end_padding": end_padding,
        }

    @staticmethod
    def _handwriting_line_timing_plan(
        lines,
        letter_delay,
        configured_return_duration,
    ):
        if not lines:
            raise AnimationTemplateError(
                "Handwriting pen requires at least one rendered text line."
            )

        letter_delay = float(letter_delay)

        if letter_delay <= 0:
            raise AnimationTemplateError(
                "Handwriting letter delay must be greater than zero."
            )

        return_duration = max(
            0.0,
            float(configured_return_duration),
        )
        line_timings = []
        cursor = 0.0

        for line_index, line in enumerate(lines):
            writing_duration = (
                line.visible_character_count
                * letter_delay
            )
            line_return_duration = (
                return_duration
                if line_index < len(lines) - 1
                else 0.0
            )
            end_time = (
                cursor
                + writing_duration
                + line_return_duration
            )
            line_timings.append(
                HandwritingLineTiming(
                    line_index=line_index,
                    start_time=cursor,
                    visible_character_count=(
                        line.visible_character_count
                    ),
                    writing_duration=writing_duration,
                    return_duration=line_return_duration,
                    end_time=end_time,
                )
            )
            cursor = end_time

        return HandwritingTimingPlan(
            letter_delay=letter_delay,
            lines=tuple(line_timings),
        )

    @staticmethod
    def _handwriting_motion_segments(
        lines,
        timing_plan,
    ):
        if len(lines) != len(timing_plan.lines):
            raise AnimationTemplateError(
                "Handwriting geometry and timing line counts differ."
            )

        segments = []

        for line_index, (line, line_timing) in enumerate(
            zip(lines, timing_plan.lines)
        ):
            segments.append(
                HandwritingMotionSegment(
                    kind="write",
                    line_index=line_index,
                    by_x=line.width,
                    by_y=0.0,
                    duration=line_timing.writing_duration,
                )
            )

            if line_index >= len(lines) - 1:
                continue

            next_line = lines[line_index + 1]
            segments.append(
                HandwritingMotionSegment(
                    kind="line_return",
                    line_index=None,
                    by_x=next_line.left - line.right,
                    by_y=next_line.top - line.top,
                    duration=line_timing.return_duration,
                )
            )

        return tuple(segments)

    def _create_handwriting_pen(
        self,
        slide,
        first_line,
        spec,
    ):
        pen_spec = spec.handwriting_pen
        shape_name = (
            f"{spec.shape_name}_HANDWRITING_PEN"
        )

        if self.locator.find_all(slide, shape_name):
            raise AnimationTemplateError(
                "Rendered presentation already contains "
                f"generated shape '{shape_name}'."
            )

        normalized_image_path = self.asset_normalizer.prepare(
            pen_spec.image_path,
            alpha_threshold=pen_spec.alpha_threshold,
            background_tolerance=(
                pen_spec.background_tolerance
            ),
        )
        left = first_line.left + pen_spec.offset_x
        top = first_line.top + pen_spec.offset_y
        pen_shape = slide.Shapes.AddPicture(
            FileName=str(normalized_image_path),
            LinkToFile=False,
            SaveWithDocument=True,
            Left=left,
            Top=top,
            Width=-1,
            Height=-1,
        )
        pen_shape.Name = shape_name
        pen_shape.LockAspectRatio = self.MSO_TRUE
        pen_shape.Width = pen_spec.width
        pen_shape.Left = left
        pen_shape.Top = top
        pen_shape.ZOrder(self.BRING_TO_FRONT)

        return pen_shape

    def _handwriting_fallback_reason(
        self,
        pen_spec,
    ):
        if pen_spec is None:
            return "handwriting pen plan is incomplete", True

        if pen_spec.fallback_effect != "text_only":
            return "configured fallback is not text_only", True

        if not pen_spec.enabled:
            return "handwriting pen is disabled", False

        if not self._is_valid_png(pen_spec.image_path):
            return (
                f"pen PNG is missing or invalid at "
                f"{pen_spec.image_path}",
                True,
            )

        return None, False

    def _rendered_text_line_bounds(self, sentence_shape):
        try:
            text_range = sentence_shape.TextFrame2.TextRange
            line_collection = text_range.Lines
            line_count = int(line_collection.Count)
        except Exception as error:
            raise AnimationTemplateError(
                "PowerPoint rendered text line bounds are unavailable."
            ) from error

        if line_count <= 0:
            raise AnimationTemplateError(
                "PowerPoint reported no rendered sentence lines."
            )

        if line_count == 1:
            return (
                self._rendered_range_bounds(
                    text_range,
                    "sentence",
                ),
            )

        lines = []

        for line_index in range(1, line_count + 1):
            line_range = self._text_line_range(
                text_range,
                line_collection,
                line_index,
            )

            lines.append(
                self._rendered_range_bounds(
                    line_range,
                    f"sentence line {line_index}",
                )
            )

        return tuple(lines)

    @staticmethod
    def _rendered_range_bounds(text_range, label):
        try:
            text = str(text_range.Text)
            visible_character_count = (
                VisualAnimationPresentationProcessor
                ._visible_character_count(text)
            )
            bounds = RenderedTextLineBounds(
                left=float(text_range.BoundLeft),
                top=float(text_range.BoundTop),
                width=float(text_range.BoundWidth),
                height=float(text_range.BoundHeight),
                text=text,
                visible_character_count=(
                    visible_character_count
                ),
            )
        except Exception as error:
            raise AnimationTemplateError(
                "PowerPoint could not provide rendered bounds for "
                f"{label}."
            ) from error

        if bounds.width <= 0 or bounds.height <= 0:
            raise AnimationTemplateError(
                f"Rendered {label} must have positive width and height."
            )

        return bounds

    @staticmethod
    def _visible_character_count(text):
        rendered_text = str(text).replace("\r", "").replace("\n", "")
        rendered_text = rendered_text.replace("\v", "")
        return max(
            1,
            len(rendered_text),
        )

    @staticmethod
    def _text_line_range(
        text_range,
        line_collection,
        line_index,
    ):
        getters = (
            lambda: text_range.Lines(line_index, 1),
            lambda: line_collection.Item(line_index),
            lambda: line_collection(line_index),
        )

        for get_line in getters:
            try:
                return get_line()
            except Exception:
                continue

        raise AnimationTemplateError(
            f"PowerPoint could not access rendered sentence line "
            f"{line_index}."
        )

    @staticmethod
    def _is_valid_png(image_path):
        image_path = Path(image_path)

        if not image_path.is_file():
            return False

        try:
            with image_path.open("rb") as image_file:
                return (
                    image_file.read(8)
                    == b"\x89PNG\r\n\x1a\n"
                )
        except OSError:
            return False

    def _create_reveal_mask(
        self,
        slide,
        sentence_shape,
        spec,
    ):
        mask_name = (
            f"{spec.shape_name}_REVEAL_MASK"
        )

        if self.locator.find_all(slide, mask_name):
            raise AnimationTemplateError(
                "Rendered presentation already contains "
                f"generated shape '{mask_name}'."
            )

        left = float(sentence_shape.Left)
        top = float(sentence_shape.Top)
        width = float(sentence_shape.Width)
        height = float(sentence_shape.Height)

        if width <= 0 or height <= 0:
            raise AnimationTemplateError(
                f"Semantic sentence shape '{spec.shape_name}' "
                "must have positive width and height."
            )

        mask = slide.Shapes.AddShape(
            self.RECTANGLE_SHAPE,
            left,
            top,
            width,
            height,
        )
        mask.Name = mask_name
        mask.Fill.Solid()
        mask.Fill.ForeColor.RGB = (
            self._mask_fill_color(
                slide,
                spec.mask_color,
            )
        )
        mask.Fill.Transparency = 0.0
        mask.Line.Visible = self.MSO_FALSE
        mask.ZOrder(self.BRING_TO_FRONT)

        return mask

    def _mask_fill_color(
        self,
        slide,
        configured_color,
    ):
        try:
            background_fill = slide.Background.Fill

            if background_fill.Type == self.SOLID_FILL:
                return int(
                    background_fill.ForeColor.RGB
                )
        except Exception:
            pass

        if configured_color is None:
            raise AnimationTemplateError(
                "Sentence reveal mask has neither a usable "
                "slide background color nor a configured color."
            )

        return int(configured_color)

    @staticmethod
    def _motion_distance_percent(
        distance,
        slide_dimension,
        allow_negative=False,
        allow_zero=False,
    ):
        distance = float(distance)
        slide_dimension = float(slide_dimension)

        invalid_distance = (
            distance < 0
            if allow_zero
            else distance <= 0
        )

        if allow_negative:
            invalid_distance = (
                distance == 0 and not allow_zero
            )

        if invalid_distance or slide_dimension <= 0:
            raise AnimationTemplateError(
                "Sentence motion requires valid movement and "
                "positive slide dimensions."
            )

        return (distance / slide_dimension) * 100.0

    @staticmethod
    def _slide_width(slide):
        width_getters = (
            lambda: slide.Parent.PageSetup.SlideWidth,
            lambda: slide.Parent.Parent.PageSetup.SlideWidth,
            lambda: (
                slide.Application.ActivePresentation
                .PageSetup.SlideWidth
            ),
        )

        for get_width in width_getters:
            try:
                width = float(get_width())

                if width > 0:
                    return width
            except Exception:
                continue

        raise AnimationTemplateError(
            "Could not determine the PowerPoint slide width "
            "for sentence reveal motion."
        )

    @staticmethod
    def _slide_height(slide):
        height_getters = (
            lambda: slide.Parent.PageSetup.SlideHeight,
            lambda: slide.Parent.Parent.PageSetup.SlideHeight,
            lambda: (
                slide.Application.ActivePresentation
                .PageSetup.SlideHeight
            ),
        )

        for get_height in height_getters:
            try:
                height = float(get_height())

                if height > 0:
                    return height
            except Exception:
                continue

        raise AnimationTemplateError(
            "Could not determine the PowerPoint slide height "
            "for sentence handwriting motion."
        )

    def _add_effect(
        self,
        sequence,
        shape,
        effect_id,
        insertion_index,
    ):
        if insertion_index is None:
            return sequence.AddEffect(
                shape,
                effect_id,
                self.ANIMATION_LEVEL_NONE,
                self.WITH_PREVIOUS,
            )

        return sequence.AddEffect(
            shape,
            effect_id,
            self.ANIMATION_LEVEL_NONE,
            self.WITH_PREVIOUS,
            insertion_index,
        )

    @staticmethod
    def _delete_effect(effect):
        if effect is None:
            return

        try:
            effect.Delete()
        except Exception:
            pass

    @staticmethod
    def _delete_shape(shape):
        if shape is None:
            return

        try:
            shape.Delete()
        except Exception:
            pass
