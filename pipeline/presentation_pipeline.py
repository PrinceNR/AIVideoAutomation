from pathlib import Path
from presentation.presentation_builder import PresentationBuilder
from utils.file_manager import FileManager
from config import PRESENTATION_TEMPLATE_PATH
from presentation.presentation_logger import (
    presentation_logger as log,
)


class PresentationPipeline:

    def __init__(
        self,
        file_manager=None,
        builder=None,
    ):
        self.file_manager = file_manager or FileManager()
        self.builder = builder or PresentationBuilder()

    def run(self, lesson_path=None):

        log.info("\n========================================")
        log.info("STAGE 2 - PRESENTATION GENERATION")
        log.info("========================================")

        # -------------------------------------------------
        # Get lesson
        # -------------------------------------------------

        # If main.py provides a lesson path,
        # use that exact lesson.
        if lesson_path is not None:
            lesson_path = Path(lesson_path)

            log.detail(f"Using lesson: {lesson_path}")

        # If running Stage 2 independently,
        # find the latest lesson.
        else:
            lesson_path = self._find_latest_lesson()

            if lesson_path is not None:
                log.detail(f"Latest lesson: {lesson_path}")

        if lesson_path is None or not lesson_path.exists():
            raise FileNotFoundError(
                "No lesson.json found.\n"
                "Please run Stage 1 first:\n\n"
                "python -m pipeline.vocabulary_pipeline"
            )

        lesson_folder = lesson_path.parent

        # -------------------------------------------------
        # Load lesson
        # -------------------------------------------------

        lesson = self.file_manager.load_lesson(
            lesson_path
        )

        slide_count = self.builder.get_slide_count(
            lesson
        )

        log.info(f"\nTopic: {lesson_folder.name}")
        log.info(f"Words: {len(lesson.words)}")
        log.info(f"Slides: {slide_count}")

        # -------------------------------------------------
        # Template
        # -------------------------------------------------

        template_path = Path(
            PRESENTATION_TEMPLATE_PATH
        )

        if not template_path.exists():
            raise FileNotFoundError(
                f"Template not found: {template_path}"
            )

        # -------------------------------------------------
        # Output
        # -------------------------------------------------

        presentation_folder = (
            lesson_folder / "presentation"
        )

        presentation_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        output_path = (
            presentation_folder /
            f"{lesson_folder.name}.pptx"
        )

        log.detail(f"Output: {output_path}")

        # -------------------------------------------------
        # Build presentation
        # -------------------------------------------------

        summary = self.builder.build(
            lesson,
            template_path,
            output_path
        )

        log.info("\nRendering slides... OK")
        log.info("Progress bars... OK")
        log.info(
            "Embedding audio... "
            f"{summary.audio_files} files"
        )
        log.info(
            "Embedding videos... "
            f"{summary.video_clips} silent autoplay clips"
        )
        log.info(
            "Applying visual animations... "
            f"{summary.animation_slides} slides"
        )
        log.info("Applying slide timings... OK")
        log.info("\nPresentation created successfully!")

        log.info("\n========================================")
        log.info("STAGE 2 COMPLETED")
        log.info("========================================")

        log.info(f"\nOutput: {output_path}")

        return output_path

    def _find_latest_lesson(self):

        output_folder = Path("output")

        if not output_folder.exists():
            return None

        lessons = list(
            output_folder.glob("*/lesson.json")
        )

        if not lessons:
            return None

        return max(
            lessons,
            key=lambda path: path.stat().st_mtime
        )


if __name__ == "__main__":

    pipeline = PresentationPipeline()

    pipeline.run()
