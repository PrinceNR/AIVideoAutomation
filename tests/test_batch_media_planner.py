from models.word import Word

from media_engine.batch_media_planner import (
    BatchMediaPlanner
)


def create_word(
    word,
    meaning,
    part_of_speech,
    sentence
):

    return Word(
        word=word,
        meaning=meaning,
        pronunciation="",
        part_of_speech=part_of_speech,
        difficulty="",
        translations={},

        present_sentence=sentence,
        past_sentence="",
        future_sentence="",

        base_form="",
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
            "yellow",
            "having the color of lemons",
            "adjective",
            "She wears a yellow dress."
        ),

        create_word(
            "ambivalent",
            "having mixed or conflicting feelings",
            "adjective",
            "She feels ambivalent about the decision."
        ),

        create_word(
            "nod",
            "to move the head up and down",
            "verb",
            "He nods his head in agreement."
        ),

        create_word(
            "shiver",
            "to shake slightly because of cold or fear",
            "verb",
            "She shivers in the cold."
        )
    ]

    planner = BatchMediaPlanner()

    plans = planner.plan(
        words
    )

    for word, plan in zip(
        words,
        plans
    ):

        print(
            f"\nWord: {word.word}"
        )

        print(
            f"Type: "
            f"{plan.preferred_type.value}"
        )

        print(
            f"Requires motion: "
            f"{plan.requires_motion}"
        )

        print(
            f"Reason: "
            f"{plan.reason}"
        )


if __name__ == "__main__":
    main()