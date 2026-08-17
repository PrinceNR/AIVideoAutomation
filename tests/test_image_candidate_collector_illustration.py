from pathlib import Path

from image_engine.image_candidate_collector import (
    ImageCandidateCollector
)

from image_engine.image_candidate_type import (
    ImageCandidateType
)


def main():

    collector = (
        ImageCandidateCollector()
    )

    output_folder = Path(
        "output/"
        "test_collector_illustrations"
    )

    candidates = collector.collect(
        query="person thinking decision",
        image_folder=output_folder,
        attempt=1,
        candidate_type=(
            ImageCandidateType
            .ILLUSTRATION
        )
    )

    print(
        f"\nIllustration candidates: "
        f"{len(candidates)}"
    )

    for candidate in candidates:

        print(
            candidate.name
        )


if __name__ == "__main__":
    main()