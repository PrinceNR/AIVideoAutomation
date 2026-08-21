from pathlib import Path

from presentation.animations.visual_animation_planner import (
    AnimationTemplateError,
    VisualAnimationPlanner,
)
from presentation.automation.powerpoint_controller import (
    PowerPointController,
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
    NO_DELAY = 0.0
    MEDIA_PLAY_EFFECT = 83

    def __init__(
        self,
        planner=None,
        locator=None,
        controller_factory=None,
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
            print(
                "No template slides were available for "
                "visual animation planning."
            )
            return

        print("=" * 70)
        print("COM VISUAL ANIMATIONS")
        print("=" * 70)

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

            ppt.save()

        print(
            "\nCOM visual animation processing completed."
        )

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

                print(
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
                print(
                    f"  Slide {slide_index}: optional visual "
                    f"shape '{spec.shape_name}' "
                    "was not found; animation skipped."
                )
                continue

            if len(matches) > 1:
                print(
                    f"  Slide {slide_index}: optional visual "
                    f"shape name '{spec.shape_name}' matched "
                    f"{len(matches)} shapes; animation skipped."
                )
                continue

            shape = matches[0]

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
            print(
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
            if insertion_index is None:
                effect = sequence.AddEffect(
                    shape,
                    spec.effect_id,
                    self.ANIMATION_LEVEL_NONE,
                    self.WITH_PREVIOUS,
                )
            else:
                effect = sequence.AddEffect(
                    shape,
                    spec.effect_id,
                    self.ANIMATION_LEVEL_NONE,
                    self.WITH_PREVIOUS,
                    insertion_index,
                )

            if spec.text_unit_effect is not None:
                try:
                    converted_effect = (
                        sequence.ConvertToTextUnitEffect(
                            effect,
                            spec.text_unit_effect,
                        )
                    )

                    if converted_effect is not None:
                        effect = converted_effect

                    print(
                        f"  Slide {slide_index}: "
                        f"{spec.shape_name} uses "
                        "character reveal."
                    )

                except Exception as error:
                    print(
                        f"  Slide {slide_index}: character "
                        f"reveal for '{spec.shape_name}' "
                        "was unavailable; using Wipe from "
                        f"left instead: {error}"
                    )

            effect.Timing.TriggerType = (
                self.WITH_PREVIOUS
            )
            effect.Timing.TriggerDelayTime = (
                self.NO_DELAY
            )
            duration = spec.duration

            if anchor_duration is not None:
                duration = min(
                    duration,
                    anchor_duration,
                )

            effect.Timing.Duration = duration

            if spec.direction is not None:
                effect.EffectParameters.Direction = (
                    spec.direction
                )

            print(
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

            print(
                f"  Slide {slide_index}: visual animation "
                f"for '{spec.shape_name}' failed safely: "
                f"{error}"
            )
