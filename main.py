from pipeline.vocabulary_pipeline import VocabularyPipeline
from pipeline.presentation_pipeline import PresentationPipeline
from pipeline.video_pipeline import VideoPipeline


def main():

    print("\n========================================")
    print("VOCABULARY VIDEO AUTOMATION")
    print("========================================")

    topic = input("Enter topic: ").strip()

    count = int(
        input("Enter number of words: ")
    )

    print("\nStarting full pipeline...")

    # ---------------------------------------------
    # Stage 1
    # Lesson + Images + Audio
    # ---------------------------------------------

    vocabulary_pipeline = VocabularyPipeline()

    lesson_path = vocabulary_pipeline.run(
        topic=topic,
        count=count
    )

    # ---------------------------------------------
    # Stage 2
    # Presentation
    # ---------------------------------------------

    presentation_pipeline = PresentationPipeline()

    presentation_path = presentation_pipeline.run(
        lesson_path=lesson_path
    )

    # ---------------------------------------------
    # Stage 3
    # Video
    # ---------------------------------------------

    video_pipeline = VideoPipeline()

    video_path = video_pipeline.run(
        presentation_path=presentation_path
    )

    # ---------------------------------------------
    # Completed
    # ---------------------------------------------

    print("\n========================================")
    print("FULL PIPELINE COMPLETED")
    print("========================================")

    print(f"Topic: {topic}")
    print(f"Lesson: {lesson_path}")
    print(f"Presentation: {presentation_path}")
    print(f"Video: {video_path}")


if __name__ == "__main__":
    main()