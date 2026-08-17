from media_engine.media_plan import (
    MediaPlan
)

from media_engine.media_type import (
    MediaType
)


def main():

    plan = MediaPlan(
        preferred_type=(
            MediaType.VIDEO
        ),
        reason=(
            "The action is easier "
            "to understand through motion."
        ),
        requires_motion=True
    )

    print(
        f"Preferred type: "
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