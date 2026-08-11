from youtube_engine.youtube_auth import YouTubeAuth


def main():

    print("\n========================================")
    print("YOUTUBE AUTHENTICATION TEST")
    print("========================================")

    auth = YouTubeAuth()

    youtube = auth.authenticate()

    response = (
        youtube.channels()
        .list(
            part="snippet",
            mine=True
        )
        .execute()
    )

    channels = response.get(
        "items",
        []
    )

    if not channels:

        print(
            "Authentication succeeded, "
            "but no YouTube channel was found."
        )

        return

    channel = channels[0]

    channel_id = channel["id"]

    channel_name = (
        channel["snippet"]["title"]
    )

    print("\nAuthentication successful!")

    print(
        f"Channel: {channel_name}"
    )

    print(
        f"Channel ID: {channel_id}"
    )


if __name__ == "__main__":
    main()