from media_engine.media_plan import (
    MediaPlan
)


class MediaPlanApplier:

    def apply(
        self,
        words,
        plans: list[MediaPlan]
    ) -> None:

        if len(words) != len(plans):

            raise ValueError(
                "Word count and media plan "
                "count do not match."
            )

        for word, plan in zip(
            words,
            plans
        ):

            word.preferred_media = (
                plan.preferred_type.value
            )

            word.media_reason = (
                plan.reason
            )

            word.requires_motion = (
                plan.requires_motion
            )