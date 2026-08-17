from models.lesson_mapper import (
    LessonMapper
)


def main():

    data = {
        "title": "Test Lesson",
        "topic": "actions",
        "suggestions": "",
        "words": [
            {
                "word": "nod",
                "meaning": (
                    "to move the head "
                    "up and down"
                ),
                "pronunciation": "",
                "part_of_speech": "verb",
                "difficulty": "",
                "translations": {},

                "present_sentence":
                    "He nods his head.",

                "past_sentence": "",
                "future_sentence": "",

                "base_form": "nod",
                "present_form": "nods",
                "past_form": "nodded",

                "synonyms": [],
                "antonyms": [],

                "image_keywords": [],
                "search_query": "",

                "preferred_media":
                    "video",

                "media_reason":
                    (
                        "The meaning depends "
                        "on visible movement."
                    ),

                "requires_motion":
                    True
            }
        ]
    }

    lesson = (
        LessonMapper.from_dict(
            data
        )
    )

    word = lesson.words[0]

    print(
        f"Loaded preferred media: "
        f"{word.preferred_media}"
    )

    print(
        f"Loaded requires motion: "
        f"{word.requires_motion}"
    )

    output = (
        LessonMapper.to_dict(
            lesson
        )
    )

    saved_word = (
        output["words"][0]
    )

    print(
        f"Saved preferred media: "
        f"{saved_word['preferred_media']}"
    )

    print(
        f"Saved requires motion: "
        f"{saved_word['requires_motion']}"
    )

    print(
        f"Saved reason: "
        f"{saved_word['media_reason']}"
    )


if __name__ == "__main__":
    main()