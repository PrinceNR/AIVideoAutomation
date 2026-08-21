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

            if plan.image_search_queries:
                if len(plan.image_search_queries) != 3:
                    raise ValueError(
                        "Each media plan must include "
                        "exactly 3 image search queries."
                    )

                word.search_query = (
                    plan.image_search_queries[0]
                )

                word.image_keywords = list(
                    plan.image_search_queries[1:]
                )
