import json
from pathlib import Path

from youtube_engine.youtube_uploader import (
    YouTubeUploader
)


class YouTubeUploadPipeline:

    def __init__(self):

        self.uploader = YouTubeUploader()

    def run(
        self,
        lesson_path=None,
        video_path=None,
        thumbnail_path=None,
        metadata_path=None
    ):

        print("\n========================================")
        print("STAGE 6 - YOUTUBE UPLOAD")
        print("========================================")

        # -----------------------------------------
        # Find lesson
        # -----------------------------------------

        if lesson_path is not None:

            lesson_path = Path(
                lesson_path
            )

            print(
                f"Using lesson: {lesson_path}"
            )

        else:

            lesson_path = (
                self._find_latest_lesson()
            )

            if lesson_path is None:

                raise FileNotFoundError(
                    "No lesson.json found."
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
        # Project information
        # -----------------------------------------

        lesson_folder = (
            lesson_path.parent
        )

        topic = (
            lesson_folder.name
        )

        print(f"Topic: {topic}")

        # -----------------------------------------
        # Video
        # -----------------------------------------

        if video_path is not None:

            video_path = Path(video_path)

            print(
                f"Using video: {video_path}"
            )

        else:

            video_path = (
                lesson_folder
                / "video"
                / f"{topic}.mp4"
            )

        # video_path = (
        #     lesson_folder
        #     / "video"
        #     / f"{topic}.mp4"
        # )

        if not video_path.exists():

            raise FileNotFoundError(
                f"Video not found:\n"
                f"{video_path}\n\n"
                "Please run Stage 3 first."
            )

        # -----------------------------------------
        # Thumbnail
        # -----------------------------------------

        if thumbnail_path is not None:

            thumbnail_path = Path(
                thumbnail_path
            )

            print(
                f"Using thumbnail: "
                f"{thumbnail_path}"
            )

        else:

            thumbnail_path = (
                lesson_folder
                / "thumbnail"
                / f"{topic}_thumbnail.png"
            )

        # thumbnail_path = (
        #     lesson_folder
        #     / "thumbnail"
        #     / f"{topic}_thumbnail.png"
        # )

        if not thumbnail_path.exists():

            raise FileNotFoundError(
                f"Thumbnail not found:\n"
                f"{thumbnail_path}\n\n"
                "Please run Stage 4 first."
            )

        # -----------------------------------------
        # Metadata
        # -----------------------------------------

        if metadata_path is not None:

            metadata_path = Path(
                metadata_path
            )

            print(
                f"Using metadata: "
                f"{metadata_path}"
            )

        else:

            metadata_path = (
                lesson_folder
                / "youtube"
                / "metadata.json"
            )

        # metadata_path = (
        #     lesson_folder
        #     / "youtube"
        #     / "metadata.json"
        # )

        if not metadata_path.exists():

            raise FileNotFoundError(
                f"YouTube metadata not found:\n"
                f"{metadata_path}\n\n"
                "Please run Stage 5 first."
            )

        with open(
            metadata_path,
            "r",
            encoding="utf-8"
        ) as file:

            metadata = json.load(file)

        # -----------------------------------------
        # Display what will be uploaded
        # -----------------------------------------

        print("\nVideo:")
        print(video_path)

        print("\nThumbnail:")
        print(thumbnail_path)

        print("\nMetadata:")
        print(metadata_path)

        print("\nTitle:")
        print(
            metadata.get(
                "title",
                ""
            )
        )

        # -----------------------------------------
        # Upload
        #
        # IMPORTANT:
        # Keep PRIVATE during development.
        # -----------------------------------------

        result = self.uploader.upload(
            video_path=video_path,
            thumbnail_path=thumbnail_path,
            metadata=metadata
        )

        # -----------------------------------------
        # Save upload result
        # -----------------------------------------

        youtube_folder = (
            lesson_folder
            / "youtube"
        )

        result_path = (
            youtube_folder
            / "upload_result.json"
        )

        with open(
            result_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                result,
                file,
                indent=4,
                ensure_ascii=False
            )

        # -----------------------------------------
        # Completed
        # -----------------------------------------

        print("\n========================================")
        print("STAGE 6 COMPLETED")
        print("========================================")

        print(
            f"Video ID: "
            f"{result['video_id']}"
        )

        print(
            f"Privacy: "
            f"{result['privacy_status']}"
        )

        print(
            f"Thumbnail uploaded: "
            f"{result['thumbnail_uploaded']}"
        )

        print(
            f"Upload result: "
            f"{result_path}"
        )

        return result

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

    pipeline = YouTubeUploadPipeline()

    pipeline.run()