from video_engine.batch_video_query_generator import (
    BatchVideoQueryGenerator
)

from video_engine.video_query_applier import (
    VideoQueryApplier
)


class VideoQueryPlanningService:

    def __init__(
        self,
        query_generator=None,
        query_applier=None
    ):

        self.query_generator = (
            query_generator
            or BatchVideoQueryGenerator()
        )

        self.query_applier = (
            query_applier
            or VideoQueryApplier()
        )

    def plan_lesson(
        self,
        lesson
    ):

        video_words = [
            word
            for word in lesson.words
            if (
                word.preferred_media
                == "video"
            )
        ]

        if not video_words:

            print(
                "No video words found. "
                "Skipping video query planning."
            )

            return []

        print(
            f"Generating video queries "
            f"for {len(video_words)} word(s)..."
        )

        query_sets = (
            self.query_generator.generate(
                video_words
            )
        )

        self.query_applier.apply(
            video_words,
            query_sets
        )

        return query_sets