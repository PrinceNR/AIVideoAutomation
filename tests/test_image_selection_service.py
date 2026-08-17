from pathlib import Path

from models.word import Word

from image_engine.image_selection_service import (
    ImageSelectionService
)


def main():

    word = Word(
        word="persuade",

        meaning=(
            "to make someone agree "
            "by giving reasons"
        ),

        pronunciation="/pəˈsweɪd/",

        part_of_speech="verb",

        difficulty="Intermediate",

        translations={},

        present_sentence=(
            "She persuades him "
            "to join the team."
        ),

        past_sentence="",

        future_sentence="",

        base_form="persuade",

        present_form="persuades",

        past_form="persuaded",

        synonyms=[],

        antonyms=[],

        image_keywords=[
            "person talking to friend",
            "convincing someone",
            "sharing ideas",
            "discussion"
        ],

        search_query=(
            "friends serious discussion"
        )
    )

    service = (
        ImageSelectionService()
    )

    result = service.select(
        word=word,
        image_folder=Path(
            "output/test_image_selection"
        )
    )

    print(
        "\nFINAL RESULT"
    )

    print(
        f"Status: "
        f"{result['status']}"
    )

    print(
        f"Selected image: "
        f"{result.get('selected_image')}"
    )

    print(
        f"Selected score: "
        f"{result.get('selected_score')}"
    )

    print(
        f"Selected query: "
        f"{result.get('selected_query')}"
    )


if __name__ == "__main__":
    main()