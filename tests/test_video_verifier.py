from pathlib import Path

from models.word import Word

from video_engine.video_candidate import (
    VideoCandidate
)

from video_engine.video_verifier import (
    VideoVerifier
)


def main():

    video_folder = Path(
        "output/test_video_download"
    )

    videos = list(
        video_folder.glob(
            "*.mp4"
        )
    )

    frames = sorted(
        (
            video_folder
            / "frames"
        ).glob(
            "*.jpg"
        )
    )

    if not videos or not frames:

        print(
            "Video or extracted frames "
            "not found."
        )

        return

    video_path = videos[0]

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

    candidate = VideoCandidate(
        source="pexels",

        source_id="8170609",

        video_url="local-test",

        duration=7.0,

        width=1280,
        height=720,

        local_path=str(
            video_path
        )
    )

    verifier = (
        VideoVerifier()
    )

    result = verifier.verify(
        word=word,
        candidate=candidate,
        frame_paths=frames
    )

    print(
        "\nVIDEO VERIFICATION RESULT"
    )

    print(
        f"Score: "
        f"{result.get('score')}"
    )

    print(
        f"Suitable: "
        f"{result.get('suitable')}"
    )

    print(
        f"Motion visible: "
        f"{result.get('motion_visible')}"
    )

    print(
        f"Meaning match: "
        f"{result.get('meaning_match')}"
    )

    print(
        f"Loop suitable: "
        f"{result.get('loop_suitable')}"
    )

    print(
        f"Model: "
        f"{result.get('model_used')}"
    )

    print(
        f"Reason: "
        f"{result.get('reason')}"
    )


if __name__ == "__main__":
    main()