from models.lesson import Lesson
from models.word import Word

from media_engine.media_planning_service import (
    MediaPlanningService
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

    lesson = Lesson(
        title="Media Planning Test",
        topic="test",
        suggestions="",
        words=[
            create_word(
                "xylophone",
                (
                    "a musical instrument "
                    "with wooden bars"
                ),
                "noun",
                "The child plays the xylophone."
            ),

            create_word(
                "nod",
                (
                    "to move the head "
                    "up and down"
                ),
                "verb",
                "He nods in agreement."
            ),

            create_word(
                "ambivalent",
                (
                    "having mixed or "
                    "conflicting feelings"
                ),
                "adjective",
                (
                    "She feels ambivalent "
                    "about the decision."
                )
            )
        ]
    )

    service = (
        MediaPlanningService()
    )

    service.plan_lesson(
        lesson
    )

    for word in lesson.words:

        print(
            f"\nWord: {word.word}"
        )

        print(
            f"Preferred media: "
            f"{word.preferred_media}"
        )

        print(
            f"Requires motion: "
            f"{word.requires_motion}"
        )

        print(
            f"Reason: "
            f"{word.media_reason}"
        )


if __name__ == "__main__":
    main()