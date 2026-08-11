from pathlib import Path

from presentation.timeline.slide_timeline import SlideTimeline


def test_slide_timeline():

    timeline = SlideTimeline()

    # Audio durations from our cultivate example
    pronunciation_duration = 0.91
    pronunciation_duration_2 = 0.91
    meaning_duration = 3.47

    # ---------------------------------------------------------
    # Audio 1
    # ---------------------------------------------------------

    event1 = timeline.add_audio(
        file=Path("pronunciation.mp3"),
        duration=pronunciation_duration
    )

    # ---------------------------------------------------------
    # Audio 2
    # ---------------------------------------------------------

    event2 = timeline.add_audio(
        file=Path("pronunciation.mp3"),
        duration=pronunciation_duration_2
    )

    # ---------------------------------------------------------
    # Audio 3
    # ---------------------------------------------------------

    event3 = timeline.add_audio(
        file=Path("meaning.mp3"),
        duration=meaning_duration
    )

    # ---------------------------------------------------------
    # Print results
    # ---------------------------------------------------------

    print("\nSlide Timeline Test")
    print("-" * 40)

    print(
        f"Audio 1 start: "
        f"{event1.start_time:.2f}s"
    )

    print(
        f"Audio 2 start: "
        f"{event2.start_time:.2f}s"
    )

    print(
        f"Audio 3 start: "
        f"{event3.start_time:.2f}s"
    )

    print(
        f"Slide duration: "
        f"{timeline.duration:.2f}s"
    )

    # ---------------------------------------------------------
    # Verify expected values
    # ---------------------------------------------------------

    assert round(event1.start_time, 2) == 0.50

    assert round(event2.start_time, 2) == 1.71

    assert round(event3.start_time, 2) == 2.92

    assert round(timeline.duration, 2) == 6.39

    print("\nTimeline test passed!")


if __name__ == "__main__":
    test_slide_timeline()