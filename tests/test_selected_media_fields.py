from models.lesson import Lesson
from models.word import Word
from models.lesson_mapper import (
    LessonMapper
)


def main():

    word = Word(
        word="wave",
        meaning="to move the hand to greet someone",
        pronunciation="",
        part_of_speech="verb",
        difficulty="",
        translations={},

        present_sentence="She waves her hand.",
        past_sentence="",
        future_sentence="",

        base_form="wave",
        present_form="waves",
        past_form="waved",

        synonyms=[],
        antonyms=[],

        image_keywords=[],
        search_query="",

        preferred_media="video",
        requires_motion=True,

        media_type="video",

        video_folder=(
            "output/test/videos/wave"
        ),

        default_video=(
            "output/test/videos/wave/"
            "selected.mp4"
        )
    )

    lesson = Lesson(
        title="Test",
        topic="actions",
        suggestions="",
        words=[word]
    )

    data = LessonMapper.to_dict(
        lesson
    )

    restored = (
        LessonMapper.from_dict(
            data
        )
    )

    restored_word = (
        restored.words[0]
    )

    print(
        f"Preferred media: "
        f"{restored_word.preferred_media}"
    )

    print(
        f"Actual media type: "
        f"{restored_word.media_type}"
    )

    print(
        f"Video folder: "
        f"{restored_word.video_folder}"
    )

    print(
        f"Default video: "
        f"{restored_word.default_video}"
    )


if __name__ == "__main__":
    main()