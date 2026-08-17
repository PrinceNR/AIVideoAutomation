from pathlib import Path
import json

from models.word import Word

from image_engine.image_downloader import (
    ImageDownloader
)

from video_engine.video_selection_service import (
    VideoSelectionService
)


class MediaSelectionService:

    def __init__(
        self,
        video_selection_service=None,
        image_downloader=None
    ):

        self.video_selection_service = (
            video_selection_service
            or VideoSelectionService()
        )

        self.image_downloader = (
            image_downloader
            or ImageDownloader()
        )

    def process_word(
        self,
        word: Word,
        lesson_folder: Path
    ) -> dict:

        lesson_folder = Path(
            lesson_folder
        )

        print(
            f"\nProcessing media for: "
            f"{word.word}"
        )

        print(
            f"Preferred media: "
            f"{word.preferred_media}"
        )

        if word.preferred_media == "video":

            return self._process_video(
                word=word,
                lesson_folder=lesson_folder
            )

        return self._process_image(
            word=word,
            lesson_folder=lesson_folder
        )

    def _process_video(
        self,
        word: Word,
        lesson_folder: Path
    ) -> dict:

        video_folder = (
            lesson_folder
            / "videos"
            / word.word.lower()
        )

        word.video_folder = str(
            video_folder
        )

        print(
            f"Trying video media for: "
            f"{word.word}"
        )

        result = (
            self.video_selection_service.select(
                word=word,
                output_folder=video_folder
            )
        )

        if result.get("status") == "selected":

            word.default_video = (
                result.get(
                    "selected_video"
                )
            )

            word.default_image = (
                result.get(
                    "preview_image"
                )
            )

            word.media_type = "video"

            result["final_media_type"] = (
                "video"
            )

            print(
                f"\nSelected video: "
                f"{word.default_video}"
            )

            print(
                f"Video score: "
                f"{result.get('selected_score', 0)}"
            )

            print(
                "Actual media type: video"
            )

        else:

            word.default_video = None

            print(
                f"\nNo suitable video found "
                f"for {word.word}."
            )

            print(
                "Falling back to image..."
            )

            self.image_downloader.download_word_images(
                word,
                lesson_folder
            )

            result["final_media_type"] = (
                word.media_type
            )

            result["fallback_image"] = (
                word.default_image
            )

        self._save_video_report(
            video_folder=video_folder,
            result=result
        )

        return result

    def _process_image(
        self,
        word: Word,
        lesson_folder: Path
    ) -> dict:

        self.image_downloader.download_word_images(
            word,
            lesson_folder
        )

        return {
            "status":
                "image_processed",

            "final_media_type":
                word.media_type,

            "default_image":
                word.default_image
        }

    @staticmethod
    def _save_video_report(
        video_folder: Path,
        result: dict
    ) -> None:

        video_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        report_path = (
            video_folder
            / "video_selection_report.json"
        )

        with open(
            report_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                result,
                file,
                ensure_ascii=False,
                indent=4
            )