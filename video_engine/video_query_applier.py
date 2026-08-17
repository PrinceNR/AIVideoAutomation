class VideoQueryApplier:

    def apply(
        self,
        words,
        query_sets: list[list[str]]
    ) -> None:

        if len(words) != len(query_sets):

            raise ValueError(
                "Word count and video query "
                "count do not match."
            )

        for word, queries in zip(
            words,
            query_sets
        ):

            word.video_search_queries = list(
                queries
            )