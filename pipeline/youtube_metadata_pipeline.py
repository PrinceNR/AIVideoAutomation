import json
from pathlib import Path

from utils.file_manager import FileManager
from ai.youtube_metadata_generator import (
    generate_youtube_metadata
)


class YouTubeMetadataPipeline:

    def __init__(self):

        self.file_manager = FileManager()

    def run(
        self,
        lesson_path=None
    ):

        print("\n========================================")
        print("STAGE 5 - YOUTUBE METADATA")
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
                    "Please run Stage 1 first."
                )

            print(
                f"Latest lesson: "
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

        topic = (
            lesson_folder.name
            .replace("_", " ")
        )

        print(f"Topic: {topic}")

        print(
            f"Words: {len(lesson.words)}"
        )

        # -----------------------------------------
        # Generate metadata
        # -----------------------------------------

        print(
            "\nGenerating YouTube metadata..."
        )

        metadata = (
            generate_youtube_metadata(
                topic=topic,
                lesson=lesson
            )
        )

        # -----------------------------------------
        # Basic validation
        # -----------------------------------------

        title = metadata.get(
            "title",
            ""
        ).strip()

        description = metadata.get(
            "description",
            ""
        ).strip()

        tags = metadata.get(
            "tags",
            []
        )

        hashtags = metadata.get(
            "hashtags",
            []
        )

        if not title:
            raise ValueError(
                "YouTube title is empty."
            )

        if len(title) > 100:
            title = title[:100].rstrip()

        metadata["title"] = title
        metadata["description"] = description
        metadata["tags"] = tags
        metadata["hashtags"] = hashtags

        # -----------------------------------------
        # YouTube folder
        # -----------------------------------------

        youtube_folder = (
            lesson_folder
            / "youtube"
        )

        youtube_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        metadata_path = (
            youtube_folder
            / "metadata.json"
        )

        # -----------------------------------------
        # Save JSON
        # -----------------------------------------

        with open(
            metadata_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                metadata,
                file,
                indent=4,
                ensure_ascii=False
            )

        # -----------------------------------------
        # Display result
        # -----------------------------------------

        print("\nTitle:")
        print(title)

        print("\nDescription:")
        print(description)

        print("\nTags:")
        print(", ".join(tags))

        print("\nHashtags:")
        print(" ".join(hashtags))

        print("\n========================================")
        print("STAGE 5 COMPLETED")
        print("========================================")

        print(
            f"Metadata: {metadata_path}"
        )

        return metadata_path

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

    pipeline = YouTubeMetadataPipeline()

    pipeline.run()