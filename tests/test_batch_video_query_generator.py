from models.word import Word

from video_engine.batch_video_query_generator import (
    BatchVideoQueryGenerator
)


def create_word(
    word,
    meaning,
    sentence
):

    return Word(
        word=word,
        meaning=meaning,
        pronunciation="",
        part_of_speech="verb",
        difficulty="",
        translations={},

        present_sentence=sentence,
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

        create_word(
            "nod",
            (
                "to move the head up and down "
                "to show agreement"
            ),
            "He nods his head in agreement."
        ),

        create_word(
            "shiver",
            (
                "to shake slightly because "
                "of cold or fear"
            ),
            "She shivers in the cold."
        ),

        create_word(
            "stretch",
            (
                "to extend the body or limbs"
            ),
            "He stretches his arms."
        )
    ]

    generator = (
        BatchVideoQueryGenerator()
    )

    query_sets = generator.generate(
        words
    )

    for word, queries in zip(
        words,
        query_sets
    ):

        print(
            f"\nWord: {word.word}"
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