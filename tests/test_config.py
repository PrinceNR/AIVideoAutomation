from config import (
    OUTPUT_FOLDER,
    IMAGE_COUNT,
    IMAGE_FORMAT,
    PRESENTATION_TEMPLATE_PATH,
    THUMBNAIL_TEMPLATE_PATH,
    THUMBNAIL_MAX_WORDS,
    THUMBNAIL_WIDTH,
    THUMBNAIL_HEIGHT,
    AUDIO_INITIAL_DELAY,
    AUDIO_GAP,
    YOUTUBE_PRIVACY_STATUS,
    YOUTUBE_MADE_FOR_KIDS,
    YOUTUBE_CATEGORY_ID,
    YOUTUBE_NOTIFY_SUBSCRIBERS,
    YOUTUBE_CLIENT_SECRET_PATH,
    YOUTUBE_TOKEN_PATH,
)


def main():

    print("\n========================================")
    print("CONFIGURATION TEST")
    print("========================================")

    print("Output folder:", OUTPUT_FOLDER)

    print("\nImage")
    print("Count:", IMAGE_COUNT)
    print("Format:", IMAGE_FORMAT)

    print("\nPresentation")
    print("Template:", PRESENTATION_TEMPLATE_PATH)

    print("\nThumbnail")
    print("Template:", THUMBNAIL_TEMPLATE_PATH)
    print("Max words:", THUMBNAIL_MAX_WORDS)
    print(
        "Size:",
        THUMBNAIL_WIDTH,
        "x",
        THUMBNAIL_HEIGHT
    )

    print("\nAudio")
    print("Initial delay:", AUDIO_INITIAL_DELAY)
    print("Gap:", AUDIO_GAP)

    print("\nYouTube")
    print("Privacy:", YOUTUBE_PRIVACY_STATUS)
    print("Made for kids:", YOUTUBE_MADE_FOR_KIDS)
    print("Category:", YOUTUBE_CATEGORY_ID)
    print(
        "Notify subscribers:",
        YOUTUBE_NOTIFY_SUBSCRIBERS
    )

    print("\nYouTube Auth")
    print(
        "Client secret:",
        YOUTUBE_CLIENT_SECRET_PATH
    )
    print(
        "Token:",
        YOUTUBE_TOKEN_PATH
    )


if __name__ == "__main__":
    main()