from pathlib import Path

from models.word import Word

from image_engine.image_fallback_service import (
    ImageFallbackService
)


class FakeSelectionService:

    def __init__(self):
        self.calls = []

    def select(
        self,
        word,
        image_folder,
        per_source,
        candidate_type
    ):

        self.calls.append(
            candidate_type.value
        )

        return {
            "status": "selected",
            "candidate_type":
                candidate_type.value,
            "selected_image":
                "test.jpg",
            "selected_score": 90
        }


def make_word(
    word_text,
    preferred_media
):

    return Word(
        word=word_text,
        meaning="test",
        pronunciation="",
        part_of_speech="noun",
        difficulty="",
        translations={},

        present_sentence="Test.",
        past_sentence="",
        future_sentence="",

        base_form=word_text,
        present_form=word_text,
        past_form=word_text,

        synonyms=[],
        antonyms=[],

        image_keywords=[],
        search_query="",

        preferred_media=preferred_media
    )


def main():

    # ---------------------------------
    # ILLUSTRATION FIRST
    # ---------------------------------

    fake_service = (
        FakeSelectionService()
    )

    fallback_service = (
        ImageFallbackService(
            selection_service=fake_service
        )
    )

    word = make_word(
        "ambivalent",
        "illustration"
    )

    result = fallback_service.select(
        word=word,
        image_folder=Path(
            "output/test"
        )
    )

    print(
        "Illustration preference calls:",
        fake_service.calls
    )

    print(
        "Selected type:",
        result.get("candidate_type")
    )

    # ---------------------------------
    # PHOTO FIRST
    # ---------------------------------

    fake_service = (
        FakeSelectionService()
    )

    fallback_service = (
        ImageFallbackService(
            selection_service=fake_service
        )
    )

    word = make_word(
        "backpack",
        "photo"
    )

    result = fallback_service.select(
        word=word,
        image_folder=Path(
            "output/test"
        )
    )

    print(
        "Photo preference calls:",
        fake_service.calls
    )

    print(
        "Selected type:",
        result.get("candidate_type")
    )


if __name__ == "__main__":
    main()