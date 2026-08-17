from models.word import Word

from video_engine.video_search_service import (
    VideoSearchService
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
        VideoSearchService()
    )

    result = service.search(
        word
    )

    print(
        "\nFINAL RESULT"
    )

    print(
        f"Status: "
        f"{result.get('status')}"
    )

    print(
        f"Successful query: "
        f"{result.get('query')}"
    )

    candidates = result.get(
        "candidates",
        []
    )

    print(
        f"Candidates: "
        f"{len(candidates)}"
    )

    for index, candidate in enumerate(
        candidates,
        start=1
    ):

        print(
            f"\nCandidate {index}"
        )

        print(
            f"Source: "
            f"{candidate.source}"
        )

        print(
            f"Duration: "
            f"{candidate.duration}s"
        )

        print(
            f"Resolution: "
            f"{candidate.width}x"
            f"{candidate.height}"
        )


if __name__ == "__main__":
    main()