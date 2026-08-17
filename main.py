import json
from pipeline.vocabulary_pipeline import VocabularyPipeline
from pipeline.presentation_pipeline import PresentationPipeline
from pipeline.video_pipeline import VideoPipeline
from pipeline.thumbnail_pipeline import ThumbnailPipeline
from pipeline.youtube_metadata_pipeline import YouTubeMetadataPipeline
from pipeline.youtube_upload_pipeline import YouTubeUploadPipeline

from config import (
    YOUTUBE_PRIVACY_STATUS,
    YOUTUBE_MADE_FOR_KIDS,
    YOUTUBE_CATEGORY_ID,
    YOUTUBE_NOTIFY_SUBSCRIBERS,
)



def confirm_youtube_upload(
    metadata_path,
    video_path,
    thumbnail_path
):

    # ---------------------------------------------
    # Load generated metadata
    # ---------------------------------------------

    with open(
        metadata_path,
        "r",
        encoding="utf-8"
    ) as file:

        metadata = json.load(file)

    title = metadata.get(
        "title",
        ""
    )

    # ---------------------------------------------
    # Display final review
    # ---------------------------------------------

    print("\n========================================")
    print("READY FOR YOUTUBE")
    print("========================================")

    print(f"\nTitle:")
    print(title)

    print(f"\nVideo:")
    print(video_path)

    print(f"\nThumbnail:")
    print(thumbnail_path)

    print("\nUpload Settings:")
    print("Privacy: private")
    print("Made for kids: False")

    print("\n========================================")

    # ---------------------------------------------
    # Confirmation
    # ---------------------------------------------

    while True:

        choice = input(
            "Upload to YouTube? (y/n): "
        ).strip().lower()

        if choice in ["y", "yes"]:
            return True

        if choice in ["n", "no"]:
            return False

        print(
            "Please enter y or n."
        )

def main():

    print("\n========================================")
    print("VOCABULARY VIDEO AUTOMATION")
    print("========================================")

    topic = input("Enter topic: ").strip()

    count = int(
        input("Enter number of words: ")
    )

    suggestions = input("Enter the suggestions for the video: ").strip()

    print("\nStarting full pipeline...")

    # ---------------------------------------------
    # Stage 1
    # Lesson + Images + Audio
    # ---------------------------------------------

    vocabulary_pipeline = VocabularyPipeline()

    lesson_path = vocabulary_pipeline.run(
        topic=topic,
        count=count,
        suggestions=suggestions
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
    # Stage 4
    # Thumbnail
    # ---------------------------------------------

    thumbnail_pipeline = ThumbnailPipeline()

    thumbnail_path = thumbnail_pipeline.run(
        lesson_path=lesson_path
    )

    # ---------------------------------------------
    # Stage 5
    # YouTube Metadata
    # ---------------------------------------------

    youtube_metadata_pipeline = (
        YouTubeMetadataPipeline()
    )

    metadata_path = (
        youtube_metadata_pipeline.run(
            lesson_path=lesson_path
        )
    )

    

    # # ---------------------------------------------
    # # Stage 6
    # # YouTube Upload
    # # ---------------------------------------------

    # youtube_upload_pipeline = (
    #     YouTubeUploadPipeline()
    # )

    # upload_result = (
    #     youtube_upload_pipeline.run(
    #         lesson_path=lesson_path,
    #         video_path=video_path,
    #         thumbnail_path=thumbnail_path,
    #         metadata_path=metadata_path
    #     )
    # )

    # ---------------------------------------------
    # Final YouTube Review
    # ---------------------------------------------

    should_upload = confirm_youtube_upload(
        metadata_path=metadata_path,
        video_path=video_path,
        thumbnail_path=thumbnail_path
    )


    # ---------------------------------------------
    # Stage 6
    # YouTube Upload
    # ---------------------------------------------

    upload_result = None

    if should_upload:

        youtube_upload_pipeline = (
            YouTubeUploadPipeline()
        )

        upload_result = (
            youtube_upload_pipeline.run(
                lesson_path=lesson_path,
                video_path=video_path,
                thumbnail_path=thumbnail_path,
                metadata_path=metadata_path
            )
        )

    else:

        print("\n========================================")
        print("YOUTUBE UPLOAD SKIPPED")
        print("========================================")

        print(
            "Video and metadata were generated, "
            "but nothing was uploaded to YouTube."
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
    print(f"Thumbnail: {thumbnail_path}")
    print(f"Metadata: {metadata_path}")

    if upload_result:

        print(
            f"YouTube Video ID: "
            f"{upload_result['video_id']}"
        )

        print(
            f"Privacy: {YOUTUBE_PRIVACY_STATUS}"
        )

    else:

        print(
            "YouTube: Not uploaded"
        )


if __name__ == "__main__":
    main()