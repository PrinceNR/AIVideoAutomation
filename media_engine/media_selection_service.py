from pathlib import Path
import json

from models.word import Word

from image_engine.image_downloader import (
    ImageDownloader
)

from video_engine.video_selection_service import (
    VideoSelectionService
)
from media_engine.adaptive_media_recovery_planner import (
    AdaptiveMediaRecoveryPlanner
)


class MediaSelectionService:

    def __init__(
        self,
        video_selection_service=None,
        image_downloader=None,
        recovery_planner=None
    ):

        self.video_selection_service = (
            video_selection_service
            or VideoSelectionService()
        )

        self.image_downloader = (
            image_downloader
            or ImageDownloader()
        )

        self.recovery_planner = (
            recovery_planner
            or AdaptiveMediaRecoveryPlanner()
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

                result = self._process_video(
                    word=word,
                    lesson_folder=lesson_folder
                )

            else:
                result = self._process_image(
                    word=word,
                    lesson_folder=lesson_folder
                )

            if (
                word.media_status == "media_missing"
                and not self._recovery_was_attempted(
                    word
                )
            ):
                return self._attempt_recovery(
                    word=word,
                    lesson_folder=lesson_folder,
                    initial_result=result
                )

            return result

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

    def _attempt_recovery(
        self,
        word,
        lesson_folder,
        initial_result
    ):

        attempted_queries = (
            self._collect_attempted_queries(
                word,
                initial_result
            )
        )

        word.media_recovery = {
            "attempted": True,
            "status": "planning",
            "attempted_queries": attempted_queries
        }

        print(
            f"\nPlanning one adaptive media "
            f"recovery for: {word.word}"
        )

        plan = self.recovery_planner.plan(
            word,
            attempted_queries
        )

        recovery_type = plan.media_type.value

        word.media_recovery.update({
            "media_type": recovery_type,
            "reason": plan.reason,
            "search_queries": list(
                plan.search_queries
            )
        })

        print(
            "Adaptive recovery media type: "
            f"{recovery_type}"
        )

        if recovery_type == "video":
            recovery_result = (
                self._recover_with_video(
                    word,
                    lesson_folder,
                    plan.search_queries
                )
            )
        else:
            recovery_result = (
                self._recover_with_image(
                    word,
                    lesson_folder,
                    recovery_type,
                    plan.search_queries
                )
            )

        word.media_recovery["status"] = (
            word.media_status
        )

        result = dict(initial_result)
        result["status"] = word.media_status
        result["media_status"] = word.media_status
        result["final_media_type"] = word.media_type
        result["adaptive_recovery"] = (
            recovery_result
        )

        return result

    def _recover_with_video(
        self,
        word,
        lesson_folder,
        search_queries
    ):

        original_queries = list(
            word.video_search_queries
        )
        word.video_search_queries = list(
            search_queries
        )

        video_folder = (
            Path(lesson_folder)
            / "videos"
            / word.word.lower()
        )
        word.video_folder = str(video_folder)

        try:
            result = self.video_selection_service.select(
                word=word,
                output_folder=video_folder
            )
        finally:
            word.video_search_queries = (
                original_queries
            )

        status = result.get("status")

        if status == "selected":
            word.default_video = result.get(
                "selected_video"
            )
            word.default_image = result.get(
                "preview_image"
            )
            word.media_type = "video"
            word.media_status = "fallback_selected"
        elif status == "verification_unavailable":
            word.media_status = "verification_unavailable"
        elif status == "error":
            word.media_status = "error"
        else:
            word.media_status = "media_missing"

        return result

    def _recover_with_image(
        self,
        word,
        lesson_folder,
        recovery_type,
        search_queries
    ):

        original_preferred_media = (
            word.preferred_media
        )
        original_search_query = (
            word.search_query
        )
        original_image_keywords = list(
            word.image_keywords
        )

        word.preferred_media = recovery_type
        word.search_query = search_queries[0]
        word.image_keywords = list(
            search_queries[1:]
        )

        try:
            result = (
                self.image_downloader.download_word_images(
                    word,
                    lesson_folder
                )
                or {}
            )
        finally:
            word.preferred_media = (
                original_preferred_media
            )
            word.search_query = original_search_query
            word.image_keywords = (
                original_image_keywords
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
            word.media_status = "fallback_selected"
        elif status == "verification_unavailable":
            word.media_status = "verification_unavailable"
        elif status == "error":
            word.media_status = "error"
        else:
            word.media_status = "media_missing"

        return result

    @staticmethod
    def _recovery_was_attempted(word):

        recovery = getattr(
            word,
            "media_recovery",
            {}
        ) or {}

        return bool(
            recovery.get("attempted")
        )

    @classmethod
    def _collect_attempted_queries(
        cls,
        word,
        result
    ):

        candidates = [
            word.search_query,
            *word.image_keywords,
            *word.video_search_queries
        ]

        def collect(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    if (
                        key in ("query", "selected_query")
                        and isinstance(item, str)
                    ):
                        candidates.append(item)

                    collect(item)

            elif isinstance(value, list):
                for item in value:
                    collect(item)

        collect(result)

        normalized = []
        seen = set()

        for query in candidates:
            if not isinstance(query, str):
                continue

            clean_query = " ".join(
                query.strip().split()
            )

            if not clean_query:
                continue

            key = clean_query.lower()

            if key in seen:
                continue

            seen.add(key)
            normalized.append(clean_query)

        return normalized

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
