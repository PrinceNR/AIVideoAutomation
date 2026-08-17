from pathlib import Path

from models.word import Word

from video_engine.video_selection_service import (
    VideoSelectionService
)


def main():

    word = Word(
        word="nod",

        meaning=(
            "to move the head "
            "up and down"
        ),

        pronunciation="",
        part_of_speech="verb",
        difficulty="",

        translations={},

        present_sentence=(
            "He nods his head "
            "in agreement."
        ),

        past_sentence="",
        future_sentence="",

        base_form="nod",
        present_form="nods",
        past_form="nodded",

        synonyms=[],
        antonyms=[],

        image_keywords=[
            "person nodding head",
            "head nod agreement",
            "person saying yes gesture"
        ],

        search_query=(
            "person nodding head"
        )
    )

    service = (
        VideoSelectionService()
    )

    result = service.select(
        word=word,

        output_folder=Path(
            "output/"
            "test_video_selection"
        )
    )

    print(
        "\nFINAL VIDEO RESULT"
    )

    print(
        f"Status: "
        f"{result.get('status')}"
    )

    print(
        f"Selected video: "
        f"{result.get('selected_video')}"
    )

    print(
        f"Score: "
        f"{result.get('selected_score')}"
    )

    print(
        f"Query: "
        f"{result.get('selected_query')}"
    )

    print(
        f"Source: "
        f"{result.get('source')}"
    )

    print(
        f"Loop suitable: "
        f"{result.get('loop_suitable')}"
    )


if __name__ == "__main__":
    main()