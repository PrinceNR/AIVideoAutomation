from pathlib import Path
from presentation.presentation_builder import PresentationBuilder
from utils.file_manager import FileManager
from config import PRESENTATION_TEMPLATE_PATH


class PresentationPipeline:

    def __init__(self):
        self.file_manager = FileManager()
        self.builder = PresentationBuilder()

    def run(self, lesson_path=None):

        print("\n========================================")
        print("STAGE 2 - PRESENTATION GENERATION")
        print("========================================")

        # -------------------------------------------------
        # Get lesson
        # -------------------------------------------------

        # If main.py provides a lesson path,
        # use that exact lesson.
        if lesson_path is not None:
            lesson_path = Path(lesson_path)

            print(f"Using lesson: {lesson_path}")

        # If running Stage 2 independently,
        # find the latest lesson.
        else:
            lesson_path = self._find_latest_lesson()

            if lesson_path is not None:
                print(f"Latest lesson: {lesson_path}")

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

        print(f"Topic: {lesson_folder.name}")
        print(f"Words: {len(lesson.words)}")

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

        print(f"Output: {output_path}")

        # -------------------------------------------------
        # Build presentation
        # -------------------------------------------------

        self.builder.build(
            lesson,
            template_path,
            output_path
        )

        print("\n========================================")
        print("STAGE 2 COMPLETED")
        print("========================================")

        print(f"Presentation: {output_path}")

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