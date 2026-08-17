from models.word import Word

from video_engine.video_query_applier import (
    VideoQueryApplier
)


def create_word(
    word: str
) -> Word:

    return Word(
        word=word,
        meaning="",
        pronunciation="",
        part_of_speech="verb",
        difficulty="",
        translations={},

        present_sentence="",
        past_sentence="",
        future_sentence="",

        base_form=word,
        present_form="",
        past_form="",

        synonyms=[],
        antonyms=[],

        image_keywords=[],
        search_query=""
    )


def main():

    words = [
        create_word("nod"),
        create_word("shiver")
    ]

    query_sets = [
        [
            "person nodding head",
            "man nodding yes",
            "woman nodding agreement"
        ],
        [
            "person shivering cold",
            "woman shaking from cold",
            "man shivering outside"
        ]
    ]

    applier = (
        VideoQueryApplier()
    )

    applier.apply(
        words,
        query_sets
    )

    for word in words:

        print(
            f"\nWord: {word.word}"
        )

        for index, query in enumerate(
            word.video_search_queries,
            start=1
        ):

            print(
                f"{index}. {query}"
            )


if __name__ == "__main__":
    main()