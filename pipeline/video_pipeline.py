from pathlib import Path

from presentation.exporter.video_exporter import VideoExporter


class VideoPipeline:

    def __init__(self):
        self.video_exporter = VideoExporter()

    def run(self, presentation_path=None):

        print("\n========================================")
        print("STAGE 3 - VIDEO GENERATION")
        print("========================================")

        # -------------------------------------------------
        # Get presentation
        # -------------------------------------------------

        # If main.py provides the presentation,
        # use that exact presentation.
        if presentation_path is not None:

            presentation_path = Path(
                presentation_path
            )

            print(
                f"Using presentation: "
                f"{presentation_path}"
            )

            # Expected structure:
            #
            # output/topic/presentation/topic.pptx

            presentation_folder = (
                presentation_path.parent
            )

            lesson_folder = (
                presentation_folder.parent
            )

            topic = lesson_folder.name

        # -------------------------------------------------
        # Standalone Stage 3
        # -------------------------------------------------

        else:

            lesson_path = self._find_latest_lesson()

            if lesson_path is None:
                raise FileNotFoundError(
                    "No lesson.json found.\n"
                    "Please run Stage 1 first:\n\n"
                    "python -m pipeline.vocabulary_pipeline"
                )

            lesson_folder = lesson_path.parent

            topic = lesson_folder.name

            print(
                f"Latest lesson: {lesson_path}"
            )

            print(
                f"Topic: {topic}"
            )

            presentation_path = (
                lesson_folder
                / "presentation"
                / f"{topic}.pptx"
            )

        # -------------------------------------------------
        # Validate presentation
        # -------------------------------------------------

        if not presentation_path.exists():

            raise FileNotFoundError(
                f"Presentation not found: "
                f"{presentation_path}\n\n"
                "Please run Stage 2 first:\n\n"
                "python -m pipeline.presentation_pipeline"
            )

        print(
            f"Presentation found: "
            f"{presentation_path}"
        )

        # -------------------------------------------------
        # Create video folder
        # -------------------------------------------------

        video_folder = (
            lesson_folder / "video"
        )

        video_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        # -------------------------------------------------
        # Final video path
        # -------------------------------------------------

        output_video = (
            video_folder /
            f"{topic}.mp4"
        )

        print(
            f"Video output: "
            f"{output_video}"
        )

        # -------------------------------------------------
        # Export PPTX -> MP4
        # -------------------------------------------------

        self.video_exporter.export(
            pptx_path=presentation_path,
            output_video=output_video
        )

        print("\n========================================")
        print("STAGE 3 COMPLETED")
        print("========================================")

        print(
            f"Video: {output_video}"
        )

        return output_video

    def _find_latest_lesson(self):

        output_folder = Path("output")

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
            key=lambda path: path.stat().st_mtime
        )


if __name__ == "__main__":

    pipeline = VideoPipeline()

    pipeline.run()