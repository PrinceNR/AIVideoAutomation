from pathlib import Path

from models.word import Word

from image_engine.image_fallback_service import (
    ImageFallbackService
)


def main():

    word = Word(
        word="hesitate",

        meaning=(
            "to pause before doing something "
            "because you are unsure"
        ),

        pronunciation="/ˈhezɪteɪt/",

        part_of_speech="verb",

        difficulty="Intermediate",

        translations={},

        present_sentence=(
            "She hesitates before "
            "making the decision."
        ),

        past_sentence="",
        future_sentence="",

        base_form="hesitate",
        present_form="hesitates",
        past_form="hesitated",

        synonyms=[],
        antonyms=[],

        image_keywords=[
            "person unsure decision",
            "person thinking choices",
            "confused person deciding"
        ],

        search_query=(
            "person unsure decision"
        )
    )

    service = (
        ImageFallbackService()
    )

    result = service.select(
        word=word,
        image_folder=Path(
            "output/"
            "test_image_fallback"
        )
    )

    print("\nFINAL RESULT")

    print(
        f"Status: "
        f"{result.get('status')}"
    )

    print(
        f"Type: "
        f"{result.get('candidate_type')}"
    )

    print(
        f"Selected image: "
        f"{result.get('selected_image')}"
    )

    print(
        f"Score: "
        f"{result.get('selected_score')}"
    )

    print(
        f"Query: "
        f"{result.get('selected_query')}"
    )

if __name__ == "__main__":
    main()