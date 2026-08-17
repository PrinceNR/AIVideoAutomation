from models.word import Word

from media_engine.media_plan import (
    MediaPlan
)

from media_engine.media_type import (
    MediaType
)

from media_engine.media_plan_applier import (
    MediaPlanApplier
)


def main():

    word = Word(
        word="nod",
        meaning="to move the head up and down",
        pronunciation="",
        part_of_speech="verb",
        difficulty="",
        translations={},

        present_sentence=(
            "He nods his head."
        ),
        past_sentence="",
        future_sentence="",

        base_form="nod",
        present_form="nods",
        past_form="nodded",

        synonyms=[],
        antonyms=[],

        image_keywords=[],
        search_query=""
    )

    plan = MediaPlan(
        preferred_type=(
            MediaType.VIDEO
        ),
        reason=(
            "The meaning depends "
            "on visible movement."
        ),
        requires_motion=True
    )

    applier = MediaPlanApplier()

    applier.apply(
        [word],
        [plan]
    )

    print(
        f"Word: {word.word}"
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