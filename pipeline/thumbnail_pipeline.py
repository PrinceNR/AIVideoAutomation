from pathlib import Path

from utils.file_manager import FileManager

from thumbnail_engine.thumbnail_pptx_generator import (
    ThumbnailPptxGenerator
)

from thumbnail_engine.thumbnail_png_exporter import (
    ThumbnailPngExporter
)

class ThumbnailPipeline:

    def __init__(self):

        self.file_manager = FileManager()

        self.pptx_generator = (
            ThumbnailPptxGenerator()
        )

        self.png_exporter = (
            ThumbnailPngExporter()
        )

    def run(
        self,
        lesson_path=None
    ):

        print("\n========================================")
        print("STAGE 4 - THUMBNAIL GENERATION")
        print("========================================")

        # -----------------------------------------
        # Lesson
        # -----------------------------------------

        if lesson_path is not None:

            lesson_path = Path(
                lesson_path
            )

            print(
                f"Using lesson: "
                f"{lesson_path}"
            )

        else:

            lesson_path = (
                self._find_latest_lesson()
            )

            if lesson_path is None:

                raise FileNotFoundError(
                    "No lesson.json found.\n"
                    "Please run Stage 1 first:\n\n"
                    "python -m "
                    "pipeline.vocabulary_pipeline"
                )

            print(
                f"Latest lesson: "
                f"{lesson_path}"
            )

        if not lesson_path.exists():

            raise FileNotFoundError(
                f"Lesson not found: "
                f"{lesson_path}"
            )

        # -----------------------------------------
        # Load lesson
        # -----------------------------------------

        lesson = (
            self.file_manager.load_lesson(
                lesson_path
            )
        )

        lesson_folder = (
            lesson_path.parent
        )

        topic = lesson_folder.name

        print(f"Topic: {topic}")

        print(
            f"Words available: "
            f"{len(lesson.words)}"
        )

        # -----------------------------------------
        # Template
        # -----------------------------------------

        template_path = Path(
            "templates/"
            "thumbnail/"
            "thumbnail_template.pptx"
        )

        if not template_path.exists():

            raise FileNotFoundError(
                f"Thumbnail template "
                f"not found: "
                f"{template_path}"
            )

        # -----------------------------------------
        # Output folder
        # -----------------------------------------

        thumbnail_folder = (
            lesson_folder
            / "thumbnail"
        )

        thumbnail_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        # -----------------------------------------
        # PPTX output
        # -----------------------------------------

        pptx_output = (
            thumbnail_folder
            / f"{topic}_thumbnail.pptx"
        )

        # -----------------------------------------
        # PNG output
        # -----------------------------------------

        png_output = (
            thumbnail_folder
            / f"{topic}_thumbnail.png"
        )

        # =========================================
        # Create editable PPTX
        # =========================================

        self.pptx_generator.generate(
            lesson=lesson,
            lesson_folder=lesson_folder,
            template_path=template_path,
            output_path=pptx_output
        )

        # =========================================
        # Export PNG
        # =========================================

        self.png_exporter.export(
            pptx_path=pptx_output,
            output_path=png_output,
            width=1280,
            height=720
        )

        # -----------------------------------------
        # Completed
        # -----------------------------------------

        print("\n========================================")
        print("STAGE 4 COMPLETED")
        print("========================================")

        print(
            f"Editable PPTX: "
            f"{pptx_output}"
        )

        print(
            f"PNG: "
            f"{png_output}"
        )

        return png_output
        

    def _find_latest_lesson(
        self
    ):

        output_folder = Path(
            "output"
        )

        if not output_folder.exists():
            return None

        lessons = list(
            output_folder.glob(
                "*/lesson.json"
            )
        )

        if not lessons:
            return None

        return max(
            lessons,
            key=lambda path:
            path.stat().st_mtime
        )


if __name__ == "__main__":

    pipeline = ThumbnailPipeline()

    pipeline.run()