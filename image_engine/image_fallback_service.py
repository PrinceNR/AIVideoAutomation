from pathlib import Path

from models.word import Word

from image_engine.image_selection_service import (
    ImageSelectionService
)

from image_engine.image_candidate_type import (
    ImageCandidateType
)

from config import IMAGE_COUNT


class ImageFallbackService:

    def __init__(
        self,
        selection_service=None
    ):

        self.selection_service = (
            selection_service
            or ImageSelectionService()
        )

    def select(
        self,
        word: Word,
        image_folder: Path,
        per_source: int = IMAGE_COUNT
    ) -> dict:

        # -----------------------------------------
        # 1. Try normal stock photos first
        # -----------------------------------------

        print(
            f"\nTrying photo media for: "
            f"{word.word}"
        )

        photo_result = (
            self.selection_service.select(
                word=word,
                image_folder=image_folder,
                per_source=per_source,
                candidate_type=(
                    ImageCandidateType.PHOTO
                )
            )
        )

        if (
            photo_result.get("status")
            == "selected"
        ):

            return self._build_result(
                final_result=photo_result,
                photo_result=photo_result
            )

        # Gemini unavailable:
        # don't waste another Gemini request.
        if (
            photo_result.get("status")
            == "verification_unavailable"
        ):

            return self._build_result(
                final_result=photo_result,
                photo_result=photo_result
            )

        # -----------------------------------------
        # 2. Photos failed → try illustrations
        # -----------------------------------------

        print(
            f"\nNo suitable photo found "
            f"for {word.word}."
        )

        print(
            "Trying illustrations..."
        )

        illustration_result = (
            self.selection_service.select(
                word=word,
                image_folder=image_folder,
                per_source=per_source,
                candidate_type=(
                    ImageCandidateType.ILLUSTRATION
                )
            )
        )

        return self._build_result(
            final_result=illustration_result,
            photo_result=photo_result,
            illustration_result=illustration_result
        )

    def _build_result(
        self,
        final_result: dict,
        photo_result: dict,
        illustration_result: dict | None = None
    ) -> dict:

        result = dict(
            final_result
        )

        result["media_attempts"] = {
            "photo": photo_result,
            "illustration": (
                illustration_result
            )
        }

        return result