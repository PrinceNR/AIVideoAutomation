from pathlib import Path

from image_engine.image_candidate_collector import (
    ImageCandidateCollector
)


def main():

    collector = (
        ImageCandidateCollector()
    )

    test_folder = Path(
        "output/test_image_candidates"
    )

    candidates = collector.collect(
        query="friends serious discussion",
        image_folder=test_folder,
        attempt=1
    )

    print(
        f"\nDownloaded candidates: "
        f"{len(candidates)}"
    )

    for candidate in candidates:

        print(
            candidate.name
        )


if __name__ == "__main__":
    main()