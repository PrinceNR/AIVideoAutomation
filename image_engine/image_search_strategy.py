from models.word import Word


class ImageSearchStrategy:

    def __init__(
        self,
        max_queries: int = 3
    ):
        self.max_queries = max_queries

    def build_queries(
        self,
        word: Word
    ) -> list[str]:

        candidates = []

        # -----------------------------------------
        # 1. Primary Gemini-generated search query
        # -----------------------------------------

        if word.search_query:

            candidates.append(
                word.search_query
            )

        # -----------------------------------------
        # 2. Image keyword fallbacks
        # -----------------------------------------

        if word.image_keywords:

            candidates.extend(
                word.image_keywords
            )

        # -----------------------------------------
        # 3. Final generic fallback
        # -----------------------------------------

        if word.word:

            candidates.append(
                word.word
            )

        # -----------------------------------------
        # Normalize + remove duplicates
        # -----------------------------------------

        queries = self._normalize_queries(
            candidates
        )

        return queries[
            :self.max_queries
        ]

    def _normalize_queries(
        self,
        queries
    ) -> list[str]:

        normalized = []
        seen = set()

        for query in queries:

            if not isinstance(
                query,
                str
            ):
                continue

            # Remove extra spaces
            clean_query = " ".join(
                query.strip().split()
            )

            if not clean_query:
                continue

            key = (
                clean_query.lower()
            )

            if key in seen:
                continue

            seen.add(
                key
            )

            normalized.append(
                clean_query
            )

        return normalized