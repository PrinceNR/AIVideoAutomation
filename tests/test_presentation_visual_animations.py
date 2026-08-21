import io
import unittest
from contextlib import redirect_stdout

from pptx.enum.shapes import MSO_SHAPE_TYPE

from presentation.animations.visual_animation_planner import (
    AnimationTemplateError,
    VisualAnimationPlanner,
    VisualAnimationSpec,
)
from presentation.animations.visual_animation_presentation_processor import (
    VisualAnimationPresentationProcessor,
)


class FakeTiming:

    def __init__(self, trigger_type, delay, duration):
        self.TriggerType = trigger_type
        self.TriggerDelayTime = delay
        self.Duration = duration


class FakeEffectParameters:

    def __init__(self):
        self.Direction = None


class FakeEffect:

    def __init__(
        self,
        shape=None,
        effect_id=None,
        trigger_type=3,
        delay=0.0,
        duration=0.0,
        sequence=None,
    ):
        self.Shape = shape
        self.EffectType = effect_id
        self.Timing = FakeTiming(
            trigger_type,
            delay,
            duration,
        )
        self.EffectParameters = FakeEffectParameters()
        self.TextUnitEffect = None
        self.sequence = sequence

    def Delete(self):
        self.sequence.effects.remove(self)


class FakeSequence:

    def __init__(
        self,
        effects=None,
        add_failure=False,
        conversion_failure=False,
    ):
        self.effects = list(effects or [])
        self.add_failure = add_failure
        self.conversion_failure = conversion_failure

        for effect in self.effects:
            effect.sequence = self

    @property
    def Count(self):
        return len(self.effects)

    def Item(self, index):
        return self.effects[index - 1]

    def AddEffect(
        self,
        shape,
        effect_id,
        level,
        trigger,
        index=None,
    ):
        if self.add_failure:
            raise RuntimeError("COM AddEffect failed")

        effect = FakeEffect(
            shape=shape,
            effect_id=effect_id,
            trigger_type=trigger,
            sequence=self,
        )

        if index is None:
            self.effects.append(effect)
        else:
            self.effects.insert(index - 1, effect)

        return effect

    def ConvertToTextUnitEffect(
        self,
        effect,
        text_unit_effect,
    ):
        if self.conversion_failure:
            raise RuntimeError(
                "text-unit conversion unavailable"
            )

        effect.TextUnitEffect = text_unit_effect

        return effect


class FakeCollection:

    def __init__(self, items=None):
        self.items = list(items or [])

    @property
    def Count(self):
        return len(self.items)

    def Item(self, index):
        return self.items[index - 1]


class FakeShape:

    def __init__(self, name, shape_type=1, children=None):
        self.Name = name
        self.Type = shape_type
        self.GroupItems = FakeCollection(children)


class FakeTransition:

    def __init__(self):
        self.EntryEffect = 999
        self.Speed = 2
        self.AdvanceOnTime = True
        self.AdvanceTime = 7.25


class FakeSlide:

    def __init__(self, shapes=None, sequence=None):
        self.Shapes = FakeCollection(shapes)
        self.TimeLine = type(
            "FakeTimeLine",
            (),
            {"MainSequence": sequence or FakeSequence()},
        )()
        self.SlideShowTransition = FakeTransition()


class FakeTemplateShape:

    def __init__(self, name, text=""):
        self.name = name
        self.text = text
        self.has_text_frame = bool(text)
        self.shape_type = MSO_SHAPE_TYPE.AUTO_SHAPE


class FakeTemplateSlide:

    def __init__(self, shapes=None):
        self.shapes = list(shapes or [])


def audio_effect(duration=2.0, delay=0.5):
    return FakeEffect(
        effect_id=83,
        trigger_type=3,
        delay=delay,
        duration=duration,
    )


class PresentationVisualAnimationTests(unittest.TestCase):

    TEMPLATE_PATH = "templates/vocabulary_template_v3.pptx"

    def setUp(self):
        self.planner = VisualAnimationPlanner()
        self.processor = VisualAnimationPresentationProcessor(
            planner=self.planner
        )
        self.template_plans = self.planner.build_template_plan(
            self.TEMPLATE_PATH
        )

    def test_slide_1_receives_introductory_animations(self):
        specs = self.template_plans[0]

        self.assertEqual(
            {spec.semantic_element for spec in specs},
            {
                "word",
                "pronunciation",
                "meaning",
                "translation",
                "verb_form",
                "image",
            },
        )
        self.assertTrue(all(not spec.required for spec in specs))

    def test_slide_2_receives_only_past_sentence(self):
        self._assert_sentence_slide(
            2,
            "PAST_SENTENCE",
            "past_sentence",
        )

    def test_slide_3_receives_only_present_sentence(self):
        self._assert_sentence_slide(
            3,
            "PRESENT_SENTENCE",
            "present_sentence",
        )

    def test_slide_4_receives_only_future_sentence(self):
        self._assert_sentence_slide(
            4,
            "FUTURE_SENTENCE",
            "future_sentence",
        )

    def _assert_sentence_slide(
        self,
        slide_within_word,
        shape_name,
        semantic_element,
    ):
        specs = self.template_plans[slide_within_word - 1]

        self.assertEqual(len(specs), 1)
        self.assertEqual(specs[0].shape_name, shape_name)
        self.assertEqual(
            specs[0].semantic_element,
            semantic_element,
        )
        self.assertTrue(specs[0].required)
        self.assertEqual(
            specs[0].text_unit_effect,
            self.planner.TEXT_BY_CHARACTER,
        )

    def test_repeated_static_content_is_not_animated_on_slides_2_to_4(self):
        forbidden = {
            "word",
            "pronunciation",
            "meaning",
            "translation",
            "verb_form",
            "image",
        }

        for slide_plan in self.template_plans[1:]:
            with self.subTest(shape=slide_plan[0].shape_name):
                self.assertTrue(
                    forbidden.isdisjoint(
                        {
                            spec.semantic_element
                            for spec in slide_plan
                        }
                    )
                )

    def test_sentence_semantic_name_must_select_exactly_one_target(self):
        duplicate_slide = FakeTemplateSlide(
            [
                FakeTemplateShape("PAST_SENTENCE"),
                FakeTemplateShape("PAST_SENTENCE"),
            ]
        )

        with self.assertRaisesRegex(
            AnimationTemplateError,
            "exactly one.*PAST_SENTENCE",
        ):
            self.planner.plan_slide(duplicate_slide, 2)

    def test_missing_required_sentence_shape_raises_template_error(self):
        with self.assertRaisesRegex(
            AnimationTemplateError,
            "PRESENT_SENTENCE",
        ):
            self.planner.plan_slide(FakeTemplateSlide(), 3)

    def test_fade_applies_only_to_first_slide_of_each_word(self):
        fade_slides = [
            slide_index
            for slide_index in range(1, 41)
            if self.planner.transition_spec(
                self.planner.slide_within_word(slide_index)
            ).entry_effect
            == self.planner.FADE_TRANSITION
        ]

        self.assertEqual(
            fade_slides,
            list(range(1, 41, 4)),
        )

    def test_slides_2_to_4_have_no_transition(self):
        for slide_within_word in (2, 3, 4):
            with self.subTest(
                slide_within_word=slide_within_word
            ):
                slide = FakeSlide()
                before_advance = (
                    slide.SlideShowTransition.AdvanceOnTime,
                    slide.SlideShowTransition.AdvanceTime,
                )

                self.processor.process_slide(
                    slide,
                    [],
                    slide_within_word,
                    slide_within_word,
                )

                self.assertEqual(
                    slide.SlideShowTransition.EntryEffect,
                    self.planner.NO_TRANSITION,
                )
                self.assertEqual(
                    (
                        slide.SlideShowTransition.AdvanceOnTime,
                        slide.SlideShowTransition.AdvanceTime,
                    ),
                    before_advance,
                )

    def test_audio_timing_metadata_and_order_remain_unchanged(self):
        audio_effects = [
            audio_effect(0.91, 0.5),
            audio_effect(3.47, 0.3),
        ]
        sequence = FakeSequence(audio_effects)
        slide = FakeSlide(
            shapes=[FakeShape("Intro Word")],
            sequence=sequence,
        )
        before = [
            (
                effect.Timing.TriggerType,
                effect.Timing.TriggerDelayTime,
                effect.Timing.Duration,
            )
            for effect in audio_effects
        ]
        spec = VisualAnimationSpec(
            shape_name="Intro Word",
            semantic_element="word",
            effect_id=self.planner.WIPE_EFFECT,
            duration=0.25,
            direction=self.planner.LEFT_DIRECTION,
        )

        self.processor.process_slide(slide, [spec], 1, 1)

        after = [
            (
                effect.Timing.TriggerType,
                effect.Timing.TriggerDelayTime,
                effect.Timing.Duration,
            )
            for effect in audio_effects
        ]
        remaining_audio = [
            effect
            for effect in sequence.effects
            if effect.EffectType == 83
        ]

        self.assertEqual(before, after)
        self.assertEqual(remaining_audio, audio_effects)
        self.assertEqual(
            slide.SlideShowTransition.AdvanceTime,
            7.25,
        )

    def test_sentence_uses_character_reveal_with_wipe_fallback_effect(self):
        sentence_spec = self.template_plans[1][0]
        sequence = FakeSequence(
            [audio_effect(duration=3.0)]
        )
        slide = FakeSlide(
            shapes=[FakeShape("PAST_SENTENCE")],
            sequence=sequence,
        )

        self.processor.process_slide(
            slide,
            [sentence_spec],
            2,
            2,
        )

        visual_effect = sequence.effects[1]

        self.assertEqual(
            visual_effect.TextUnitEffect,
            self.planner.TEXT_BY_CHARACTER,
        )
        self.assertEqual(
            visual_effect.EffectType,
            self.planner.WIPE_EFFECT,
        )
        self.assertEqual(
            visual_effect.Timing.TriggerType,
            self.processor.WITH_PREVIOUS,
        )
        self.assertEqual(
            visual_effect.Timing.TriggerDelayTime,
            0.0,
        )

    def test_character_conversion_failure_keeps_safe_wipe(self):
        sentence_spec = self.template_plans[2][0]
        sequence = FakeSequence(
            [audio_effect(duration=3.0)],
            conversion_failure=True,
        )
        slide = FakeSlide(
            shapes=[FakeShape("PRESENT_SENTENCE")],
            sequence=sequence,
        )
        output = io.StringIO()

        with redirect_stdout(output):
            self.processor.process_slide(
                slide,
                [sentence_spec],
                3,
                3,
            )

        visual_effect = sequence.effects[1]

        self.assertIsNone(visual_effect.TextUnitEffect)
        self.assertEqual(
            visual_effect.EffectType,
            self.planner.WIPE_EFFECT,
        )
        self.assertEqual(
            visual_effect.EffectParameters.Direction,
            self.planner.LEFT_DIRECTION,
        )
        self.assertIn(
            "using Wipe from left instead",
            output.getvalue(),
        )

    def test_progress_shapes_remain_excluded(self):
        for shape_name in (
            "PROGRESS_TRACK",
            "PROGRESS_FILL",
        ):
            with self.subTest(shape_name=shape_name):
                self.assertIsNone(
                    self.planner.plan_intro_shape(
                        shape_name,
                        "{{WORD}}",
                    )
                )

    def test_missing_optional_intro_shape_does_not_damage_timeline(self):
        audio = audio_effect()
        sequence = FakeSequence([audio])
        slide = FakeSlide(sequence=sequence)
        spec = VisualAnimationSpec(
            shape_name="Optional Intro",
            semantic_element="meaning",
            effect_id=self.planner.FADE_EFFECT,
            duration=0.20,
        )
        output = io.StringIO()

        with redirect_stdout(output):
            self.processor.process_slide(
                slide,
                [spec],
                1,
                1,
            )

        self.assertEqual(sequence.effects, [audio])
        self.assertIn("Optional Intro", output.getvalue())

    def test_missing_required_rendered_sentence_raises_template_error(self):
        sentence_spec = self.template_plans[3][0]

        with self.assertRaisesRegex(
            AnimationTemplateError,
            "FUTURE_SENTENCE",
        ):
            self.processor.process_slide(
                FakeSlide(
                    sequence=FakeSequence(
                        [audio_effect()]
                    )
                ),
                [sentence_spec],
                4,
                4,
            )


if __name__ == "__main__":
    unittest.main()
