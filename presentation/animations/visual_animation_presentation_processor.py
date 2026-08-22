from pathlib import Path

from presentation.animations.visual_animation_planner import (
    AnimationTemplateError,
    VisualAnimationPlanner,
)
from presentation.automation.powerpoint_controller import (
    PowerPointController,
)
from presentation.presentation_logger import (
    presentation_logger as log,
)


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

    ANIMATION_LEVEL_NONE = 0
    WITH_PREVIOUS = 2
    MEDIA_PLAY_EFFECT = 83
    CUSTOM_EFFECT = 0
    MOTION_BEHAVIOR = 1
    RECTANGLE_SHAPE = 1
    BRING_TO_FRONT = 0
    SOLID_FILL = 1
    MSO_FALSE = 0

    def __init__(
        self,
        planner=None,
        locator=None,
        controller_factory=None,
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
        self.debug = debug

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
                processed_slide_count += 1

            ppt.save()

        log.detail(
            "\nCOM visual animation processing completed."
        )

        return processed_slide_count

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
        insertion_index, anchor_duration = (
            self._automatic_start_group(
                sequence
            )
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

            if spec.reveal_mode == "reveal_mask":
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

    def _automatic_start_group(
        self,
        sequence,
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

                duration = float(
                    effect.Timing.Duration
                )

                if duration > 0:
                    # Insert after the first audio effect so the
                    # visuals start with it. Existing audio effects
                    # retain their relative order and timing data.
                    return index + 1, duration

            except Exception:
                continue

        # With no usable audio anchor, AddEffect safely appends.
        return None, None

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

        except Exception as error:
            self._delete_effect(effect)
            self._delete_shape(mask)
            raise AnimationTemplateError(
                "Rendered presentation slide "
                f"{slide_index} could not construct a safe "
                f"reveal mask for '{spec.shape_name}': {error}"
            ) from error

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
        mask_width,
        slide_width,
    ):
        mask_width = float(mask_width)
        slide_width = float(slide_width)

        if mask_width <= 0 or slide_width <= 0:
            raise AnimationTemplateError(
                "Sentence reveal motion requires positive mask "
                "and slide widths."
            )

        return (mask_width / slide_width) * 100.0

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
