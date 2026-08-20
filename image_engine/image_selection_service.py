from pathlib import Path
from models.word import Word
from image_engine.image_search_strategy import ImageSearchStrategy
from image_engine.image_candidate_collector import ImageCandidateCollector
from image_engine.image_candidate_type import ImageCandidateType
from image_engine.image_verifier import ImageVerifier

from config import (
    IMAGE_COUNT,
    IMAGE_VERIFICATION_MAX_CANDIDATES
)


class ImageSelectionService:

    def __init__(
        self,
        search_strategy=None,
        candidate_collector=None,
        image_verifier=None,
        max_verification_candidates=(
            IMAGE_VERIFICATION_MAX_CANDIDATES
        )
    ):

        self.search_strategy = (
            search_strategy
            or ImageSearchStrategy()
        )

        self.candidate_collector = (
            candidate_collector
            or ImageCandidateCollector()
        )

        self.image_verifier = (
            image_verifier
            or ImageVerifier()
        )

        self.max_verification_candidates = (
            max_verification_candidates
        )

    def select(
        self,
        word: Word,
        image_folder: Path,
        per_source: int = IMAGE_COUNT,
        candidate_type: ImageCandidateType = (
            ImageCandidateType.PHOTO
        )
    ) -> dict:

        queries = (
            self.search_strategy.build_queries(
                word
            )
        )

        attempts = []

        all_candidates = []
        candidate_queries = {}

        for attempt_number, query in enumerate(
            queries,
            start=1
        ):

            print(
                f"\nImage search attempt "
                f"{attempt_number}/{len(queries)}"
            )

            print(
                f"Query: {query}"
            )

            candidates = (
                self.candidate_collector.collect(
                    query=query,
                    image_folder=image_folder,
                    attempt=attempt_number,
                    per_source=per_source,
                    candidate_type=candidate_type
                )
            )

            if not candidates:

                attempts.append({
                    "attempt": attempt_number,
                    "query": query,
                    "status": "no_candidates",
                    "selected_image": None,
                    "candidate_type": candidate_type.value,
                    "selected_score": 0
                })

                continue

            attempts.append({
                "attempt": attempt_number,
                "query": query,
                "status": "collected",
                "selected_image": None,
                "candidate_type": candidate_type.value,
                "selected_score": 0
            })

            all_candidates.extend(
                candidates
            )

            for candidate in candidates:
                candidate_queries[
                    Path(candidate).name
                ] = query

        if not all_candidates:
            return {
                "status": "no_suitable_image",
                "candidate_type": candidate_type.value,
                "selected_image": None,
                "selected_score": 0,
                "best_candidate": None,
                "selected_query": None,
                "attempts": attempts
            }

        print(
            f"Collected {len(all_candidates)} "
            "image candidates."
        )

        verification_candidates = (
            self._select_verification_candidates(
                all_candidates,
                candidate_queries
            )
        )

        print(
            f"Selected "
            f"{len(verification_candidates)} "
            "candidates for Gemini verification."
        )

        verification = (
            self.image_verifier.verify(
                word,
                verification_candidates
            )
        )

        verification_status = (
            verification.get(
                "verification_status",
                "completed"
            )
        )

        # -----------------------------------------
        # Gemini temporarily unavailable
        # -----------------------------------------

        if verification_status == "unavailable":
            for attempt in attempts:
                if attempt["status"] == "collected":
                    attempt["status"] = "verification_unavailable"

            return {
                "status": "verification_unavailable",
                "candidate_type": candidate_type.value,
                "selected_image": None,
                "selected_score": 0,
                "selected_query": None,
                "attempts": attempts
            }

        selected_image = verification.get(
            "selected_image"
        )
        selected_score = verification.get(
            "selected_score",
            0
        )
        verified_candidates = verification.get(
            "candidates",
            []
        )
        selected_query = candidate_queries.get(
            selected_image
        )

        for attempt in attempts:
            if attempt["status"] != "collected":
                continue

            query_candidates = [
                candidate
                for candidate in verified_candidates
                if candidate_queries.get(
                    candidate.get("image")
                ) == attempt["query"]
            ]

            attempt["status"] = (
                "selected"
                if selected_query == attempt["query"]
                else "rejected"
            )
            attempt["selected_image"] = (
                selected_image
                if selected_query == attempt["query"]
                else None
            )
            attempt["selected_score"] = (
                max(
                    (
                        candidate.get("score", 0)
                        for candidate in query_candidates
                    ),
                    default=0
                )
            )
            attempt["model_used"] = verification.get(
                "model_used"
            )
            attempt["candidates"] = query_candidates

        best_candidate = (
            verified_candidates[0].get("image")
            if verified_candidates
            else None
        )

        if selected_image:
            print(
                "Suitable image found in batched verification."
            )

            return {
                "status": "selected",
                "selected_image": selected_image,
                "candidate_type": candidate_type.value,
                "selected_score": selected_score,
                "selected_query": selected_query,
                "attempts": attempts
            }

        print(
            f"No suitable image found. "
            f"Best score: {selected_score}"
        )

        # ---------------------------------------------
        # All queries failed quality threshold
        # ---------------------------------------------

        return {
            "status":
                "no_suitable_image",

            "candidate_type":
                candidate_type.value,

            "selected_image":
                None,

            "selected_score":
                selected_score,

            "best_candidate":
                best_candidate,

            "selected_query":
                None,

            "attempts":
                attempts
        }

    def _select_verification_candidates(
        self,
        candidates,
        candidate_queries
    ):

        if (
            len(candidates)
            <= self.max_verification_candidates
        ):
            return list(candidates)

        buckets = {}

        for candidate in candidates:
            candidate_path = Path(candidate)
            query = candidate_queries.get(
                candidate_path.name,
                "unknown"
            )
            provider = self._candidate_provider(
                candidate_path
            )
            key = (query, provider)

            buckets.setdefault(
                key,
                []
            ).append(candidate)

        selected = []
        round_index = 0

        while (
            len(selected)
            < self.max_verification_candidates
        ):
            added = False

            for bucket in buckets.values():
                if round_index >= len(bucket):
                    continue

                selected.append(
                    bucket[round_index]
                )
                added = True

                if (
                    len(selected)
                    >= self.max_verification_candidates
                ):
                    return selected

            if not added:
                break

            round_index += 1

        return selected

    @staticmethod
    def _candidate_provider(candidate_path):

        filename = candidate_path.name.lower()

        if "_pexels_" in filename:
            return "pexels"

        if "_pixabay_" in filename:
            return "pixabay"

        return "unknown"
