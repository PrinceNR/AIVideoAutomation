from models.word import Word

from image_engine.image_search_strategy import (
    ImageSearchStrategy
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
        present_sentence="",
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

    strategy = (
        ImageSearchStrategy()
    )

    queries = (
        strategy.build_queries(
            word
        )
    )

    print(
        "\nGenerated search queries:"
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