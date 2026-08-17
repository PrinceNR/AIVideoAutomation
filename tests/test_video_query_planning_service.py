from models.lesson import Lesson
from models.word import Word

from video_engine.video_query_planning_service import (
    VideoQueryPlanningService
)


def create_word(
    word,
    meaning,
    sentence,
    preferred_media
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
        search_query="",

        preferred_media=(
            preferred_media
        )
    )


def main():

    lesson = Lesson(
        title="Video Query Test",
        topic="mixed",
        suggestions="",
        words=[

            create_word(
                "nod",
                (
                    "to move the head "
                    "up and down"
                ),
                (
                    "He nods his head "
                    "in agreement."
                ),
                "video"
            ),

            create_word(
                "backpack",
                (
                    "a bag carried "
                    "on the back"
                ),
                (
                    "She carries "
                    "a backpack."
                ),
                "photo"
            ),

            create_word(
                "shiver",
                (
                    "to shake slightly "
                    "because of cold"
                ),
                (
                    "She shivers "
                    "in the cold."
                ),
                "video"
            )
        ]
    )

    service = (
        VideoQueryPlanningService()
    )

    service.plan_lesson(
        lesson
    )

    for word in lesson.words:

        print(
            f"\nWord: "
            f"{word.word}"
        )

        print(
            f"Preferred media: "
            f"{word.preferred_media}"
        )

        print(
            "Video queries:"
        )

        for query in (
            word.video_search_queries
        ):

            print(
                f"- {query}"
            )


if __name__ == "__main__":
    main()