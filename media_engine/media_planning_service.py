from media_engine.batch_media_planner import (
    BatchMediaPlanner
)

from media_engine.media_plan_applier import (
    MediaPlanApplier
)


class MediaPlanningService:

    def __init__(
        self,
        planner=None,
        plan_applier=None
    ):

        self.planner = (
            planner
            or BatchMediaPlanner()
        )

        self.plan_applier = (
            plan_applier
            or MediaPlanApplier()
        )

    def plan_lesson(
        self,
        lesson
    ):

        if not lesson.words:
            return []

        plans = self.planner.plan(
            lesson.words
        )

        self.plan_applier.apply(
            lesson.words,
            plans
        )

        return plans