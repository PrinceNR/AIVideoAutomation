import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from presentation.animations.visual_animation_presentation_processor import (
    AudioAnimationAnchor,
    RenderedTextLineBounds,
    VisualAnimationPresentationProcessor,
)
from presentation.embedders.video_embedder import VideoEmbedder
from presentation.timeline.slide_end_time import SlideEndTimeCalculator
from presentation.timeline.parallel_media_timeline import (
    ParallelMediaTimeline,
)
from presentation.timeline.slide_timeline import SlideTimeline
from presentation.video_compatibility import SilentVideoNormalizer
from presentation.video_presentation_processor import (
    SavedVideoPlaybackTarget,
    VideoPresentationProcessor,
)


class _CompletedProcess:

    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class _FakeVideoEffect:

    def __init__(self, sequence, shape, effect_type=83):
        self._sequence = sequence
        self.Shape = shape
        self.EffectType = effect_type
        self.Timing = SimpleNamespace(
            TriggerType=1,
            TriggerDelayTime=9.0,
            Duration=99.0,
        )
        play_settings = getattr(
            getattr(shape, "AnimationSettings", None),
            "PlaySettings",
            SimpleNamespace(PlayOnEntry=0),
        )
        self.EffectInformation = SimpleNamespace(
            PlaySettings=play_settings
        )

    def MoveTo(self, position):
        self._sequence.effects.remove(self)

        if getattr(self._sequence, "rebind_effects", False):
            replacement = _FakeVideoEffect(
                self._sequence,
                self.Shape,
                self.EffectType,
            )
            replacement.Timing.TriggerType = (
                self.Timing.TriggerType
            )
            replacement.Timing.TriggerDelayTime = (
                self.Timing.TriggerDelayTime
            )
            replacement.Timing.Duration = self.Timing.Duration
            self._sequence.effects.insert(position - 1, replacement)
            return

        self._sequence.effects.insert(position - 1, self)


class _FakeSequence:

    def __init__(self, effects=None, rebind_effects=False):
        self.effects = list(effects or [])
        self.rebind_effects = rebind_effects

        for effect in self.effects:
            effect._sequence = self

    @property
    def Count(self):
        return len(self.effects)

    def Item(self, index):
        return self.effects[index - 1]

    def AddEffect(self, shape, effect_id):
        effect = _FakeVideoEffect(self, shape, effect_id)
        self.effects.append(effect)
        return effect


class _FakePlaySettings:

    def __init__(self, sequence, shape):
        self._sequence = sequence
        self._shape = shape
        self._play_on_entry = 0
        self.PauseAnimation = -1
        self.LoopUntilStopped = 0
        self.HideWhileNotPlaying = -1
        self.RewindMovie = 0

    @property
    def PlayOnEntry(self):
        return self._play_on_entry

    @PlayOnEntry.setter
    def PlayOnEntry(self, value):
        self._play_on_entry = value

        if value and not any(
            effect.EffectType == 83
            and effect.Shape is self._shape
            for effect in self._sequence.effects
        ):
            self._sequence.effects.append(
                _FakeVideoEffect(self._sequence, self._shape)
            )


class _FakeMediaShape:

    def __init__(self, sequence, shape_id=20):
        self.Name = "candidate_video"
        self.Id = shape_id
        self.LockAspectRatio = None
        self.Left = None
        self.Top = None
        self.Width = None
        self.Height = None
        self.ZOrderPosition = 4
        self.MediaFormat = SimpleNamespace(Muted=0, Volume=1.0)
        self.AnimationSettings = SimpleNamespace(
            PlaySettings=_FakePlaySettings(sequence, self)
        )

    def ZOrder(self, _direction):
        self.ZOrderPosition -= 1


class _FakeMediaShapes:

    def __init__(self, slide):
        self.slide = slide
        self.created = None

    def AddMediaObject2(self, *arguments):
        self.created = _FakeMediaShape(
            self.slide.TimeLine.MainSequence
        )
        return self.created


class _FakeMediaSlide:

    def __init__(
        self,
        effects=None,
        advance_time=5.4,
        rebind_effects=False,
    ):
        self.TimeLine = SimpleNamespace(
            MainSequence=_FakeSequence(
                effects,
                rebind_effects=rebind_effects,
            )
        )
        self.Shapes = _FakeMediaShapes(self)
        self.SlideShowTransition = SimpleNamespace(
            AdvanceTime=advance_time
        )


class _FakePicture:

    def __init__(self):
        self.Name = "VOCAB_IMAGE"
        self.Left = 10.0
        self.Top = 20.0
        self.Width = 300.0
        self.Height = 200.0
        self.ZOrderPosition = 4
        self.deleted = False

    def Delete(self):
        self.deleted = True


class _RecordingEmbedder:

    def __init__(self, media_shape):
        self.media_shape = media_shape
        self.calls = []

    def embed(self, **arguments):
        self.calls.append(arguments)
        return self.media_shape


class _FakeController:

    def __init__(self, slide):
        self.presentation = SimpleNamespace(
            Slides=lambda index: slide
        )
        self.opened = None

    def __enter__(self):
        return self

    def __exit__(self, *_arguments):
        return False

    def open_presentation(self, path):
        self.opened = path


class PresentationMediaTimingTests(unittest.TestCase):

    def test_pen_and_fade_share_each_line_writing_duration(self):
        processor = VisualAnimationPresentationProcessor()
        lines = self._rendered_lines()
        plan = processor._handwriting_line_timing_plan(
            lines,
            letter_delay=0.04,
            configured_return_duration=0.12,
        )
        segments = processor._handwriting_motion_segments(
            lines,
            plan,
        )
        write_segments = [
            segment for segment in segments
            if segment.kind == "write"
        ]

        self.assertEqual(plan.letter_delay, 0.04)
        self.assertEqual(
            [line.writing_duration for line in plan.lines],
            [0.40, 0.20],
        )
        self.assertEqual(
            [segment.duration for segment in write_segments],
            [line.writing_duration for line in plan.lines],
        )

    def test_next_line_waits_for_pen_return(self):
        processor = VisualAnimationPresentationProcessor()
        plan = processor._handwriting_line_timing_plan(
            self._rendered_lines(),
            letter_delay=0.04,
            configured_return_duration=0.12,
        )

        self.assertEqual(plan.lines[0].return_duration, 0.12)
        self.assertAlmostEqual(
            plan.lines[1].start_time,
            plan.lines[0].start_time
            + plan.lines[0].writing_duration
            + plan.lines[0].return_duration,
        )

    def test_silent_mp4_is_stripped_and_cached(self):
        with tempfile.TemporaryDirectory() as temp_folder:
            source = Path(temp_folder) / "stock.mp4"
            source.write_bytes(b"source-video")
            calls = []
            normalizer = SilentVideoNormalizer(
                runner=self._silent_media_runner(calls),
                executable_finder=lambda name: name,
            )

            first = normalizer.prepare(source)
            second = normalizer.prepare(source)

        ffmpeg_calls = [
            call for call in calls if call[0] == "ffmpeg"
        ]
        self.assertEqual(first, second)
        self.assertEqual(len(ffmpeg_calls), 1)
        self.assertIn("-an", ffmpeg_calls[0])
        self.assertEqual(
            ffmpeg_calls[0][
                ffmpeg_calls[0].index("-map") + 1
            ],
            "0:v:0",
        )

    def test_gif_visual_uses_the_same_silent_mp4_policy(self):
        with tempfile.TemporaryDirectory() as temp_folder:
            source = Path(temp_folder) / "animated.gif"
            source.write_bytes(b"GIF89a")
            calls = []
            normalizer = SilentVideoNormalizer(
                runner=self._silent_media_runner(calls),
                executable_finder=lambda name: name,
            )

            output = normalizer.prepare(source)

        ffmpeg_call = next(
            call for call in calls if call[0] == "ffmpeg"
        )
        self.assertEqual(output.suffix, ".mp4")
        self.assertIn("-an", ffmpeg_call)
        self.assertIn("libx264", ffmpeg_call)

    def test_video_is_muted_autoplaying_and_looped(self):
        narration_one = self._narration_effect(
            "pronunciation", 3, 0.5, 1.0
        )
        narration_two = self._narration_effect(
            "meaning", 4, 0.2, 2.0
        )
        slide = _FakeMediaSlide(
            [narration_one, narration_two],
            rebind_effects=True,
        )
        first_timing = self._effect_timing(narration_one)
        second_snapshot = self._effect_snapshot([narration_two])

        media = VideoEmbedder().embed(
            slide=slide,
            video_path="visual.mp4",
            left=10,
            top=20,
            width=300,
            height=200,
        )

        playback = slide.TimeLine.MainSequence.Item(1)
        settings = media.AnimationSettings.PlaySettings
        self.assertTrue(settings.PlayOnEntry)
        self.assertTrue(settings.LoopUntilStopped)
        self.assertTrue(settings.RewindMovie)
        self.assertFalse(settings.PauseAnimation)
        self.assertFalse(settings.HideWhileNotPlaying)
        self.assertTrue(media.MediaFormat.Muted)
        self.assertEqual(media.MediaFormat.Volume, 0.0)
        self.assertEqual(playback.Timing.TriggerType, 2)
        self.assertEqual(playback.Timing.TriggerDelayTime, 0.0)
        self.assertEqual(narration_one.Timing.TriggerType, 2)
        self.assertEqual(
            self._effect_timing(narration_one),
            first_timing,
        )
        self.assertEqual(
            self._effect_snapshot([narration_two]),
            second_snapshot,
        )

    def test_narration_start_is_identical_for_image_and_video(self):
        image_narration = self._narration_effect(
            "meaning", 3, 0.8, 2.0
        )
        video_narration = self._narration_effect(
            "meaning", 3, 0.8, 2.0
        )
        image_start = image_narration.Timing.TriggerDelayTime
        slide = _FakeMediaSlide([video_narration])

        VideoEmbedder().embed(
            slide=slide,
            video_path="visual.mp4",
            left=10,
            top=20,
            width=300,
            height=200,
        )

        self.assertEqual(
            video_narration.Timing.TriggerDelayTime,
            image_start,
        )
        self.assertEqual(video_narration.Timing.Duration, 2.0)

    def test_video_is_not_a_teaching_timeline_prerequisite(self):
        narration = self._narration_effect(
            "meaning", 3, 0.5, 2.0
        )
        slide = _FakeMediaSlide([narration])

        media = VideoEmbedder().embed(
            slide=slide,
            video_path="visual.mp4",
            left=10,
            top=20,
            width=300,
            height=200,
        )

        media.Name = "VOCAB_IMAGE"
        sequence = slide.TimeLine.MainSequence
        self.assertEqual(sequence.Item(1).Timing.TriggerType, 2)
        self.assertEqual(sequence.Item(2).Timing.TriggerType, 2)
        self.assertTrue(ParallelMediaTimeline.is_parallel(sequence))

    def test_text_animation_start_is_not_shifted_by_video_length(self):
        for video_duration in (2.8, 8.0):
            with self.subTest(video_duration=video_duration):
                sequence = _FakeSequence()
                media = _FakeVideoEffect(
                    sequence,
                    SimpleNamespace(Name="VOCAB_IMAGE", Id=20),
                )
                media.Timing.TriggerType = 2
                media.Timing.TriggerDelayTime = 0.0
                media.Timing.Duration = 0.001
                media.SourceDuration = video_duration
                text = _FakeVideoEffect(
                    sequence,
                    SimpleNamespace(Name="PAST_SENTENCE", Id=3),
                    effect_type=10,
                )
                text.Timing.TriggerType = 3
                text.Timing.TriggerDelayTime = 0.4
                text.Timing.Duration = 1.2
                sequence.effects.extend([media, text])

                ParallelMediaTimeline.apply(sequence)

                self.assertEqual(text.Timing.TriggerType, 2)
                self.assertEqual(text.Timing.TriggerDelayTime, 0.4)
                self.assertEqual(text.Timing.Duration, 1.2)

    def test_stock_media_effect_never_becomes_narration_anchor(self):
        processor = VisualAnimationPresentationProcessor()
        sequence = _FakeSequence()
        video = _FakeVideoEffect(
            sequence,
            SimpleNamespace(Name="VOCAB_IMAGE", Id=20),
        )
        narration = self._narration_effect(
            "PAST_SENTENCE", 3, 0.5, 2.4
        )
        sequence.effects.extend([video, narration])
        video._sequence = sequence
        narration._sequence = sequence

        anchor = processor._automatic_audio_anchor(
            sequence,
            expected_shape_name="PAST_SENTENCE",
        )

        self.assertIs(anchor.effect, narration)

    def test_video_length_does_not_control_slide_advance(self):
        for video_duration in (2.8, 8.0):
            with self.subTest(video_duration=video_duration):
                slide = _FakeMediaSlide(advance_time=5.4)
                picture = _FakePicture()
                media = _FakeMediaShape(
                    slide.TimeLine.MainSequence
                )
                embedder = _RecordingEmbedder(media)
                processor = VideoPresentationProcessor(
                    video_normalizer=SimpleNamespace(
                        prepare=lambda path: Path("silent.mp4")
                    )
                )
                processor.locator = SimpleNamespace(
                    find_picture=lambda _slide: picture
                )
                processor.video_embedder = embedder

                processor._replace_picture_with_video(
                    slide=slide,
                    word=SimpleNamespace(
                        default_video="visual.mp4",
                        video_duration=video_duration,
                    ),
                    slide_index=1,
                    slide_type="vocabulary",
                )

                self.assertEqual(
                    slide.SlideShowTransition.AdvanceTime,
                    5.4,
                )
                self.assertEqual(
                    embedder.calls[0]["video_path"],
                    Path("silent.mp4"),
                )

    def test_authoritative_slide_end_uses_teaching_timeline_only(self):
        short_video_result = SlideEndTimeCalculator.calculate(
            latest_audio_end=5.4,
            latest_handwriting_end=1.8,
            end_padding=0.2,
        )
        long_video_result = SlideEndTimeCalculator.calculate(
            latest_audio_end=4.0,
            latest_handwriting_end=1.8,
            end_padding=0.2,
        )
        image_only_result = SlideEndTimeCalculator.calculate(
            latest_audio_end=4.0,
            end_padding=0.2,
        )

        self.assertAlmostEqual(short_video_result, 5.6)
        self.assertAlmostEqual(long_video_result, 4.2)
        self.assertAlmostEqual(image_only_result, 4.2)
        self.assertGreaterEqual(short_video_result, 5.4)

    def test_slide_one_narration_remains_sequential(self):
        timeline = SlideTimeline(initial_delay=0.5, audio_gap=0.2)
        pronunciation = timeline.add_audio(
            Path("pronunciation.mp3"), 1.0
        )
        repeat = timeline.add_audio(
            Path("pronunciation_repeat.mp3"), 1.0
        )
        meaning = timeline.add_audio(Path("meaning.mp3"), 2.0)

        self.assertEqual(pronunciation.start_time, 0.5)
        self.assertEqual(repeat.start_time, 1.7)
        self.assertAlmostEqual(meaning.start_time, 2.9)
        self.assertAlmostEqual(timeline.duration, 4.9)

    def test_sentence_audio_begins_after_handwriting_and_slide_outlasts_it(self):
        processor = VisualAnimationPresentationProcessor()
        audio_effect = self._narration_effect(
            "PAST_SENTENCE", 3, 0.5, 2.4
        )
        anchor = AudioAnimationAnchor(
            effect=audio_effect,
            index=1,
            duration=2.4,
            delay=0.5,
        )
        slide = _FakeMediaSlide(advance_time=2.9)

        timing = processor._reschedule_sentence_audio(
            slide=slide,
            audio_anchor=anchor,
            handwriting_start=0.5,
            handwriting_duration=1.2,
            audio_gap=0.1,
        )

        self.assertAlmostEqual(timing["handwriting_end"], 1.7)
        self.assertAlmostEqual(timing["audio_start"], 1.8)
        self.assertGreaterEqual(
            timing["slide_end"],
            timing["audio_end"],
        )
        self.assertEqual(audio_effect.Timing.Duration, 2.4)

    def test_saved_playback_verifier_preserves_media_policy(self):
        narration = self._narration_effect(
            "meaning", 3, 0.5, 3.0
        )
        slide = _FakeMediaSlide([narration], advance_time=5.4)
        media = VideoEmbedder().embed(
            slide=slide,
            video_path="visual.mp4",
            left=10,
            top=20,
            width=300,
            height=200,
        )
        media.Name = "VOCAB_IMAGE"
        controller = _FakeController(slide)
        processor = VideoPresentationProcessor(
            controller_factory=lambda visible: controller
        )
        processor.locator = SimpleNamespace(
            find_picture=lambda _slide: media
        )
        processor.saved_video_targets = {
            1: SavedVideoPlaybackTarget(
                shape_name="VOCAB_IMAGE",
                shape_id=media.Id,
                slide_advance_time=5.4,
                narration_effects=processor._narration_effects(
                    slide,
                    excluded_shape_id=media.Id,
                ),
            )
        }

        processor.verify_saved_video_playback("saved.pptx")

        self.assertEqual(controller.opened, "saved.pptx")
        self.assertEqual(
            slide.SlideShowTransition.AdvanceTime,
            5.4,
        )

    @staticmethod
    def _rendered_lines():
        return (
            RenderedTextLineBounds(
                left=100.0,
                top=200.0,
                width=250.0,
                height=20.0,
                text="ten chars!",
                visible_character_count=10,
            ),
            RenderedTextLineBounds(
                left=105.0,
                top=235.0,
                width=140.0,
                height=20.0,
                text="five!",
                visible_character_count=5,
            ),
        )

    @staticmethod
    def _silent_media_runner(calls):
        def run(command, **_arguments):
            calls.append(command)

            if command[0] == "ffmpeg":
                Path(command[-1]).write_bytes(b"silent-video")
                return _CompletedProcess()

            return _CompletedProcess(
                stdout=json.dumps(
                    {"streams": [{"codec_type": "video"}]}
                )
            )

        return run

    @staticmethod
    def _narration_effect(
        name,
        shape_id,
        delay,
        duration,
        trigger_type=3,
    ):
        effect = _FakeVideoEffect(
            sequence=None,
            shape=SimpleNamespace(Name=name, Id=shape_id),
            effect_type=83,
        )
        effect.Timing.TriggerType = trigger_type
        effect.Timing.TriggerDelayTime = delay
        effect.Timing.Duration = duration
        return effect

    @staticmethod
    def _effect_timing(effect):
        return (
            effect.Timing.TriggerDelayTime,
            effect.Timing.Duration,
        )

    @staticmethod
    def _effect_snapshot(effects):
        return [
            (
                effect.Shape.Name,
                effect.Timing.TriggerType,
                effect.Timing.TriggerDelayTime,
                effect.Timing.Duration,
            )
            for effect in effects
        ]
if __name__ == "__main__":
    unittest.main()
