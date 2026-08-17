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

        preferred_media = (
            word.preferred_media
            or "photo"
        ).lower()

        # -----------------------------------------
        # CHOOSE SEARCH ORDER
        # -----------------------------------------

        if preferred_media == "illustration":

            first_type = (
                ImageCandidateType.ILLUSTRATION
            )

            second_type = (
                ImageCandidateType.PHOTO
            )

        else:

            # Photo words use photo first.
            # Video fallback also uses photo first.
            first_type = (
                ImageCandidateType.PHOTO
            )

            second_type = (
                ImageCandidateType.ILLUSTRATION
            )

        # -----------------------------------------
        # FIRST MEDIA TYPE
        # -----------------------------------------

        first_result = self._select_type(
            word=word,
            image_folder=image_folder,
            per_source=per_source,
            candidate_type=first_type
        )

        status = first_result.get(
            "status"
        )

        if status in (
            "selected",
            "verification_unavailable"
        ):

            return self._build_result(
                final_result=first_result,

                photo_result=(
                    first_result
                    if first_type
                    == ImageCandidateType.PHOTO
                    else None
                ),

                illustration_result=(
                    first_result
                    if first_type
                    == ImageCandidateType.ILLUSTRATION
                    else None
                )
            )

        # -----------------------------------------
        # SECOND MEDIA TYPE
        # -----------------------------------------

        print(
            f"\nNo suitable "
            f"{first_type.value} found "
            f"for {word.word}."
        )

        second_result = self._select_type(
            word=word,
            image_folder=image_folder,
            per_source=per_source,
            candidate_type=second_type
        )

        photo_result = None
        illustration_result = None

        if (
            first_type
            == ImageCandidateType.PHOTO
        ):

            photo_result = first_result
            illustration_result = second_result

        else:

            illustration_result = first_result
            photo_result = second_result

        return self._build_result(
            final_result=second_result,
            photo_result=photo_result,
            illustration_result=illustration_result
        )

    def _select_type(
        self,
        word: Word,
        image_folder: Path,
        per_source: int,
        candidate_type: ImageCandidateType
    ) -> dict:

        print(
            f"\nTrying "
            f"{candidate_type.value} media "
            f"for: {word.word}"
        )

        return self.selection_service.select(
            word=word,
            image_folder=image_folder,
            per_source=per_source,
            candidate_type=candidate_type
        )

    @staticmethod
    def _build_result(
        final_result: dict,
        photo_result: dict | None = None,
        illustration_result: dict | None = None
    ) -> dict:

        result = dict(
            final_result
        )

        result["media_attempts"] = {
            "photo":
                photo_result,

            "illustration":
                illustration_result
        }

        return result