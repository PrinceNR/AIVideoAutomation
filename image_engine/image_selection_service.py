from pathlib import Path
from models.word import Word
from image_engine.image_search_strategy import ImageSearchStrategy
from image_engine.image_candidate_collector import ImageCandidateCollector
from image_engine.image_candidate_type import ImageCandidateType
from image_engine.image_verifier import ImageVerifier

from config import IMAGE_COUNT


class ImageSelectionService:

    def __init__(
        self,
        search_strategy=None,
        candidate_collector=None,
        image_verifier=None
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

        best_score = 0
        best_candidate = None

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

            verification = (
                self.image_verifier.verify(
                    word,
                    candidates
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

            if (
                verification_status
                == "unavailable"
            ):

                attempts.append({
                    "attempt": attempt_number,
                    "query": query,
                    "candidate_type": candidate_type.value,
                    "status": "verification_unavailable",
                    "selected_image": None,
                    "selected_score": 0
                })

                return {
                    "status":
                        "verification_unavailable",

                    "candidate_type": candidate_type.value,

                    "selected_image":
                        None,

                    "selected_score":
                        0,

                    "selected_query":
                        None,

                    "attempts":
                        attempts
                }

            selected_image = (
                verification.get(
                    "selected_image"
                )
            )

            selected_score = (
                verification.get(
                    "selected_score",
                    0
                )
            )

            attempts.append({
                "attempt":
                    attempt_number,

                "query":
                    query,

                "candidate_type":
                    candidate_type.value,

                "status":
                    (
                        "selected"
                        if selected_image
                        else "rejected"
                    ),

                "selected_image":
                    selected_image,

                "selected_score":
                    selected_score,

                "model_used":
                    verification.get(
                        "model_used"
                    ),

                "candidates":
                    verification.get(
                        "candidates",
                        []
                    )
            })

            # -----------------------------------------
            # Track best score even when rejected
            # -----------------------------------------

            if selected_score > best_score:

                best_score = (
                    selected_score
                )

                candidate_list = (
                    verification.get(
                        "candidates",
                        []
                    )
                )

                if candidate_list:

                    best_candidate = (
                        candidate_list[0].get(
                            "image"
                        )
                    )

            # -----------------------------------------
            # Good image found
            # -----------------------------------------

            if selected_image:

                print(
                    f"Suitable image found "
                    f"on attempt "
                    f"{attempt_number}."
                )

                return {
                    "status":
                        "selected",

                    "selected_image":
                        selected_image,

                    "candidate_type":
                        candidate_type.value,

                    "selected_score":
                        selected_score,

                    "selected_query":
                        query,

                    "attempts":
                        attempts
                }

            print(
                f"No suitable image found. "
                f"Best score: "
                f"{selected_score}"
            )

            print(
                "Trying next search query..."
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
                best_score,

            "best_candidate":
                best_candidate,

            "selected_query":
                None,

            "attempts":
                attempts
        }