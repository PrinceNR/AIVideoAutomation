from pathlib import Path
import json
from models.word import Word
from config import IMAGE_COUNT
from image_engine.image_fallback_service import ImageFallbackService



class ImageDownloader:

    def __init__(self):

        self.fallback_service = ImageFallbackService()
    def download_word_images(
        self,
        word: Word,
        lesson_folder: Path,
        per_source: int = IMAGE_COUNT
    ):

        image_folder = (
            lesson_folder
            / "images"
            / word.word.lower()
        )

        image_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        word.image_folder = str(
            image_folder
        )

        print(
            f"\nProcessing images for: "
            f"{word.word}"
        )

        result = (
            self.fallback_service.select(
                word=word,
                image_folder=image_folder,
                per_source=per_source
            )
        )

        # =============================================
        # SAVE FULL SEARCH / VERIFICATION REPORT
        # =============================================

        report_path = (
            image_folder
            / "image_selection_report.json"
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

        status = result.get(
            "status"
        )

        # =============================================
        # SUCCESS
        # =============================================

        if status == "selected":

            selected_image = (
                result.get(
                    "selected_image"
                )
            )

            selected_score = (
                result.get(
                    "selected_score",
                    0
                )
            )

            selected_query = (
                result.get(
                    "selected_query"
                )
            )
            selected_type = (
                result.get(
                    "candidate_type"
                )
            )

            selected_path = (
                image_folder
                / selected_image
            )

            word.default_image = str(
                selected_path
            )

            word.media_type = (
                selected_type
            )

            print(
                f"\nSelected image: "
                f"{selected_image}"
            )

            print(
                f"Image score: "
                f"{selected_score}"
            )

            print(
                f"Media type: "
                f"{selected_type}"
            )

            print(
                f"Successful query: "
                f"{selected_query}"
            )

            print(
                f"Image selected successfully "
                f"for {word.word}."
            )

        # =============================================
        # GEMINI TEMPORARILY UNAVAILABLE
        # =============================================

        elif (
            status
            == "verification_unavailable"
        ):

            word.default_image = None
            word.media_type = None

            print(
                f"\nImage verification "
                f"temporarily unavailable "
                f"for {word.word}."
            )

            print(
                "Candidate images were kept "
                "for later verification."
            )

        # =============================================
        # ALL SEARCH ATTEMPTS FAILED QUALITY CHECK
        # =============================================

        else:

            word.default_image = None
            word.media_type = None

            print(
                f"\nNo suitable stock image "
                f"found for {word.word}."
            )

            print(
                f"Best score: "
                f"{result.get('selected_score', 0)}"
            )

        return result
