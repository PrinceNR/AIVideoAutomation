import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import config as project_config

from pipeline.presentation_pipeline import PresentationPipeline
from presentation.animations.visual_animation_planner import (
    VisualAnimationSpec,
)
from presentation.animations.visual_animation_presentation_processor import (
    VisualAnimationPresentationProcessor,
)
from presentation.embedders.audio_embedder import AudioEmbedder
from presentation.presentation_builder import (
    PresentationBuildSummary,
)
from presentation.presentation_logger import PresentationLogger


class FakeAudioEffect:

    def __init__(self):
        self.Timing = SimpleNamespace(
            TriggerType=None,
            TriggerDelayTime=None,
            Duration=None,
        )
        self.EffectInformation = SimpleNamespace(
            PlaySettings=SimpleNamespace(
                PlayOnEntry=False
            )
        )


class FakeAudioSequence:

    def __init__(self):
        self.calls = []
        self.effect = None

    def AddEffect(self, media, effect_id):
        self.calls.append((media, effect_id))
        self.effect = FakeAudioEffect()
        return self.effect


class FakeMediaShape:
    Name = "pronunciation"
    Type = 16
    Id = 3


class FakeMediaShapes:

    def __init__(self):
        self.calls = []

    def AddMediaObject2(self, **kwargs):
        self.calls.append(kwargs)
        return FakeMediaShape()


class FakeAudioSlide:

    def __init__(self):
        self.Shapes = FakeMediaShapes()
        self.sequence = FakeAudioSequence()
        self.TimeLine = SimpleNamespace(
            MainSequence=self.sequence
        )


class FakeVisualTiming:

    def __init__(self):
        self.TriggerType = None
        self.TriggerDelayTime = None
        self.Duration = None


class FakeVisualEffect:

    def __init__(self):
        self.Timing = FakeVisualTiming()
        self.EffectParameters = SimpleNamespace(
            Direction=None
        )

    def Delete(self):
        raise AssertionError(
            "A successful visual effect must not be deleted."
        )


class FakeVisualSequence:

    def __init__(self):
        self.calls = []
        self.effect = FakeVisualEffect()

    def AddEffect(
        self,
        shape,
        effect_id,
        level,
        trigger,
        index=None,
    ):
        self.calls.append(
            (shape, effect_id, level, trigger, index)
        )
        return self.effect


class FakeFileManager:

    def __init__(self, lesson):
        self.lesson = lesson

    def load_lesson(self, lesson_path):
        return self.lesson


class FakeBuilder:

    def __init__(self, summary):
        self.summary = summary
        self.build_calls = []

    def get_slide_count(self, lesson):
        return self.summary.slides

    def build(self, lesson, template_path, output_path):
        self.build_calls.append(
            (lesson, template_path, output_path)
        )
        return self.summary


class PresentationLoggingTests(unittest.TestCase):

    def test_default_presentation_logging_is_not_verbose(self):
        self.assertFalse(
            project_config.PRESENTATION_VERBOSE_LOGGING
        )

    def test_verbose_false_suppresses_details(self):
        output = []
        logger = PresentationLogger(
            verbose=False,
            printer=output.append,
        )

        logger.detail("Audio embedded: pronunciation.mp3")
        logger.detail("Shape: pronunciation")
        logger.detail("Slide 2: PAST_SENTENCE -> reveal mask")

        self.assertEqual(output, [])

    def test_verbose_true_retains_detailed_diagnostics(self):
        output = []
        logger = PresentationLogger(
            verbose=True,
            printer=output.append,
        )

        logger.detail("Audio embedded: pronunciation.mp3")
        logger.detail("Shape: pronunciation")
        logger.detail("Animation effect created")
        logger.detail("Duration: 1.20s")

        self.assertEqual(
            output,
            [
                "Audio embedded: pronunciation.mp3",
                "Shape: pronunciation",
                "Animation effect created",
                "Duration: 1.20s",
            ],
        )

    def test_warnings_and_errors_are_visible_in_both_modes(self):
        for verbose in (False, True):
            output = []
            logger = PresentationLogger(
                verbose=verbose,
                printer=output.append,
            )

            logger.warning("Audio not found: meaning")
            logger.error("Animation construction failed")

            self.assertEqual(
                output,
                [
                    "WARNING: Audio not found: meaning",
                    "ERROR: Animation construction failed",
                ],
            )

    def test_normal_pipeline_output_keeps_concise_summary(self):
        lesson = SimpleNamespace(words=[object()] * 10)
        summary = PresentationBuildSummary(
            slides=40,
            audio_files=50,
            video_clips=0,
            animation_slides=40,
            timed_slides=40,
        )
        builder = FakeBuilder(summary)
        pipeline = PresentationPipeline(
            file_manager=FakeFileManager(lesson),
            builder=builder,
        )

        with tempfile.TemporaryDirectory() as temp_folder:
            lesson_path = Path(temp_folder) / "lesson.json"
            lesson_path.write_text("{}", encoding="utf-8")
            output = io.StringIO()

            with patch.object(
                project_config,
                "PRESENTATION_VERBOSE_LOGGING",
                False,
            ), redirect_stdout(output):
                result = pipeline.run(lesson_path)

            expected_result = (
                lesson_path.parent
                / "presentation"
                / f"{lesson_path.parent.name}.pptx"
            )

        terminal = output.getvalue()

        self.assertIn("STAGE 2 - PRESENTATION GENERATION", terminal)
        self.assertIn("Words: 10", terminal)
        self.assertIn("Slides: 40", terminal)
        self.assertIn("Rendering slides... OK", terminal)
        self.assertIn("Progress bars... OK", terminal)
        self.assertIn("Embedding audio... 50 files", terminal)
        self.assertIn(
            "Embedding videos... 0 silent autoplay clips",
            terminal,
        )
        self.assertIn(
            "Applying visual animations... 40 slides",
            terminal,
        )
        self.assertIn("Applying slide timings... OK", terminal)
        self.assertIn("STAGE 2 COMPLETED", terminal)
        self.assertNotIn("Using lesson:", terminal)
        self.assertEqual(result, expected_result)

    def test_logging_mode_does_not_change_audio_animation_or_timing_data(self):
        with tempfile.TemporaryDirectory() as temp_folder:
            audio_path = Path(temp_folder) / "pronunciation.mp3"
            audio_path.write_bytes(b"audio")

            quiet_audio, quiet_audio_output = (
                self._audio_snapshot(audio_path, False)
            )
            verbose_audio, verbose_audio_output = (
                self._audio_snapshot(audio_path, True)
            )

        quiet_visual, quiet_visual_output = (
            self._visual_snapshot(False)
        )
        verbose_visual, verbose_visual_output = (
            self._visual_snapshot(True)
        )

        self.assertEqual(quiet_audio, verbose_audio)
        self.assertEqual(quiet_visual, verbose_visual)
        self.assertEqual(quiet_audio_output, "")
        self.assertEqual(quiet_visual_output, "")
        self.assertIn("Audio embedded", verbose_audio_output)
        self.assertIn("Animation effect created", verbose_audio_output)
        self.assertIn("word -> WORD", verbose_visual_output)

    @staticmethod
    def _audio_snapshot(audio_path, verbose):
        slide = FakeAudioSlide()
        output = io.StringIO()

        with patch.object(
            project_config,
            "PRESENTATION_VERBOSE_LOGGING",
            verbose,
        ), redirect_stdout(output):
            AudioEmbedder().embed(
                slide,
                audio_path,
                start_time=0.5,
                duration=1.2,
                delay=0.5,
            )

        effect = slide.sequence.effect
        snapshot = (
            slide.sequence.calls[0][1],
            effect.Timing.TriggerType,
            effect.Timing.TriggerDelayTime,
            effect.Timing.Duration,
            effect.EffectInformation.PlaySettings.PlayOnEntry,
        )

        return snapshot, output.getvalue()

    @staticmethod
    def _visual_snapshot(verbose):
        processor = VisualAnimationPresentationProcessor()
        sequence = FakeVisualSequence()
        shape = object()
        spec = VisualAnimationSpec(
            shape_name="WORD",
            semantic_element="word",
            effect_id=10,
            duration=0.25,
        )
        output = io.StringIO()

        with patch.object(
            project_config,
            "PRESENTATION_VERBOSE_LOGGING",
            verbose,
        ), redirect_stdout(output):
            processor._append_effect(
                sequence,
                shape,
                spec,
                slide_index=1,
                insertion_index=2,
                anchor_duration=1.0,
            )

        effect = sequence.effect
        snapshot = (
            sequence.calls[0][1:],
            effect.Timing.TriggerType,
            effect.Timing.TriggerDelayTime,
            effect.Timing.Duration,
        )

        return snapshot, output.getvalue()


if __name__ == "__main__":
    unittest.main()
