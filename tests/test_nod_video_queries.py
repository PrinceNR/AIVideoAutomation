from models.word import Word

from video_engine.video_candidate_collector import (
    VideoCandidateCollector
)


def main():

    word = Word(
        word="nod",

        meaning=(
            "to move the head "
            "up and down"
        ),

        pronunciation="",
        part_of_speech="verb",
        difficulty="",

        translations={},

        present_sentence=(
            "He nods his head "
            "in agreement."
        ),

        past_sentence="",
        future_sentence="",

        base_form="nod",
        present_form="nods",
        past_form="nodded",

        synonyms=[],
        antonyms=[],

        image_keywords=[],
        search_query=""
    )

    queries = [
        "person nodding head up down",
        "man nodding yes",
        "woman nodding head agreement"
    ]

    collector = (
        VideoCandidateCollector()
    )

    for query in queries:

        print(
            f"\nTesting query: "
            f"{query}"
        )

        candidates = (
            collector.collect(
                query=query
            )
        )

        print(
            f"Short candidates: "
            f"{len(candidates)}"
        )

        for candidate in candidates:

            print(
                f"  {candidate.source} | "
                f"{candidate.duration}s | "
                f"{candidate.width}x"
                f"{candidate.height}"
            )


if __name__ == "__main__":
    main()