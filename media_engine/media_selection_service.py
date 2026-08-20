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

        selected_media = (
            self._get_valid_selected_media(
                word,
                lesson_folder
            )
        )

        if selected_media is not None:
            word.media_status = (
                word.media_status
                or self._selected_status(word)
            )

            print(
                f"\nSkipping media selection for "
                f"{word.word}; existing "
                f"{word.media_type} media is valid."
            )

            return {
                "status": "already_selected",
                "media_status": word.media_status,
                "final_media_type": word.media_type,
                "selected_media": str(selected_media)
            }

        print(
            f"\nProcessing media for: "
            f"{word.word}"
        )

        print(
            f"Preferred media: "
            f"{word.preferred_media}"
        )

        try:
            if word.preferred_media == "video":

                return self._process_video(
                    word=word,
                    lesson_folder=lesson_folder
                )

            return self._process_image(
                word=word,
                lesson_folder=lesson_folder
            )

        except Exception as error:
            word.media_status = "error"

            print(
                f"Media selection failed for "
                f"{word.word}: {error}"
            )

            return {
                "status": "error",
                "media_status": "error",
                "error": str(error)
            }

    @staticmethod
    def _get_valid_selected_media(
        word: Word,
        lesson_folder: Path
    ) -> Path | None:

        if word.media_status not in (
            None,
            "selected",
            "fallback_selected"
        ):
            return None

        if word.media_type == "video":
            saved_paths = [
                word.default_video,
                word.default_image
            ]
        elif word.media_type in (
            "photo",
            "illustration"
        ):
            saved_paths = [
                word.default_image
            ]
        else:
            return None

        resolved_paths = []

        for saved_path in saved_paths:
            if not saved_path:
                return None

            path = Path(saved_path)

            if not path.is_file() and not path.is_absolute():
                path = lesson_folder / path

            if not path.is_file():
                return None

            resolved_paths.append(path)

        return resolved_paths[0]

    @staticmethod
    def _selected_status(word: Word) -> str:

        if (
            word.preferred_media == "video"
            and word.media_type != "video"
        ):
            return "fallback_selected"

        return "selected"

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
            word.media_status = "selected"

            result["final_media_type"] = (
                "video"
            )
            result["media_status"] = (
                word.media_status
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

            if (
                result.get("status")
                == "verification_unavailable"
            ):
                print(
                    f"\nVideo verification unavailable "
                    f"for {word.word}."
                )
            elif result.get("status") == "error":
                print(
                    f"\nVideo selection failed "
                    f"for {word.word}."
                )
            else:
                print(
                    f"\nNo suitable video found "
                    f"for {word.word}."
                )

            print(
                "Falling back to image..."
            )

            image_result = (
                self.image_downloader.download_word_images(
                    word,
                    lesson_folder
                )
                or {}
            )

            image_status = image_result.get(
                "status"
            )

            if (
                image_status is None
                and self._has_valid_image(
                    word,
                    lesson_folder
                )
            ):
                image_status = "selected"

            if image_status == "selected":
                word.media_status = (
                    "fallback_selected"
                )
            elif (
                image_status
                == "verification_unavailable"
                or result.get("status")
                == "verification_unavailable"
            ):
                word.media_status = (
                    "verification_unavailable"
                )
            elif (
                image_status == "error"
                or result.get("status") == "error"
            ):
                word.media_status = "error"
            else:
                word.media_status = "media_missing"

            result["final_media_type"] = (
                word.media_type
            )

            result["fallback_image"] = (
                word.default_image
            )

            result["media_status"] = (
                word.media_status
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

        result = (
            self.image_downloader.download_word_images(
                word,
                lesson_folder
            )
            or {}
        )

        status = result.get("status")

        if (
            status is None
            and self._has_valid_image(
                word,
                lesson_folder
            )
        ):
            status = "selected"

        if status == "selected":
            word.media_status = "selected"
        elif status == "verification_unavailable":
            word.media_status = (
                "verification_unavailable"
            )
        elif status == "error":
            word.media_status = "error"
        else:
            word.media_status = "media_missing"

        return {
            "status": word.media_status,

            "media_status": word.media_status,

            "final_media_type":
                word.media_type,

            "default_image":
                word.default_image
        }

    @staticmethod
    def _has_valid_image(
        word: Word,
        lesson_folder: Path
    ) -> bool:

        if (
            word.media_type
            not in ("photo", "illustration")
            or not word.default_image
        ):
            return False

        image_path = Path(word.default_image)

        if (
            not image_path.is_file()
            and not image_path.is_absolute()
        ):
            image_path = lesson_folder / image_path

        return image_path.is_file()

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
