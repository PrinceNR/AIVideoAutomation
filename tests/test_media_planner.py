from models.word import Word

from media_engine.media_planner import (
    MediaPlanner
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
            word="yellow",
            meaning=(
                "having the color of "
                "lemons or sunlight"
            ),
            part_of_speech="adjective",
            sentence=(
                "She wears a yellow dress."
            )
        ),

        create_word(
            word="xylophone",
            meaning=(
                "a musical instrument "
                "with wooden bars"
            ),
            part_of_speech="noun",
            sentence=(
                "The child plays the xylophone."
            )
        ),

        create_word(
            word="ambivalent",
            meaning=(
                "having mixed or conflicting "
                "feelings about something"
            ),
            part_of_speech="adjective",
            sentence=(
                "She feels ambivalent "
                "about the decision."
            )
        ),

        create_word(
            word="nod",
            meaning=(
                "to move the head up and down, "
                "often to show agreement"
            ),
            part_of_speech="verb",
            sentence=(
                "He nods his head in agreement."
            )
        ),

        create_word(
            word="shiver",
            meaning=(
                "to shake slightly because "
                "of cold or fear"
            ),
            part_of_speech="verb",
            sentence=(
                "She shivers in the cold."
            )
        )
    ]

    planner = MediaPlanner()

    for word in words:

        print(
            f"\nPlanning media for: "
            f"{word.word}"
        )

        plan = planner.plan(
            word
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