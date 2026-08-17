from models.word import Word

from video_engine.video_search_strategy import (
    VideoSearchStrategy
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
        ),
        video_search_queries=[
            "man nodding yes",
            "woman nodding head agreement",
            "person nodding head up down"
        ],
    )

    strategy = (
        VideoSearchStrategy()
    )

    queries = (
        strategy.build_queries(
            word
        )
    )

    print(
        "Generated video queries:"
    )

    for index, query in enumerate(
        queries,
        start=1
    ):

        print(
            f"{index}. {query}"
        )


if __name__ == "__main__":
    main()