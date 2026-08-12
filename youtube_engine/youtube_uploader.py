import time
from pathlib import Path

from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

from youtube_engine.youtube_auth import YouTubeAuth

from config import (
    YOUTUBE_PRIVACY_STATUS,
    YOUTUBE_MADE_FOR_KIDS,
    YOUTUBE_CATEGORY_ID,
    YOUTUBE_NOTIFY_SUBSCRIBERS,
)


class YouTubeUploader:

    CATEGORY_ID = "27"

    def __init__(self):

        self.auth = YouTubeAuth()

    def upload(
        self,
        video_path,
        thumbnail_path,
        metadata,
        privacy_status= None
    ):
        if privacy_status is None:
            privacy_status = YOUTUBE_PRIVACY_STATUS

        video_path = Path(video_path).resolve()
        thumbnail_path = Path(thumbnail_path).resolve()

        # -----------------------------------------
        # Validate files
        # -----------------------------------------

        if not video_path.exists():
            raise FileNotFoundError(
                f"Video not found: {video_path}"
            )

        if not thumbnail_path.exists():
            raise FileNotFoundError(
                f"Thumbnail not found: {thumbnail_path}"
            )

        # YouTube thumbnail API maximum = 2 MB
        thumbnail_size = thumbnail_path.stat().st_size

        if thumbnail_size > 2 * 1024 * 1024:
            raise ValueError(
                "Thumbnail exceeds YouTube's 2 MB limit.\n"
                f"Current size: {thumbnail_size / 1024 / 1024:.2f} MB"
            )

        # -----------------------------------------
        # Authenticate
        # -----------------------------------------

        print("\nAuthenticating with YouTube...")

        youtube = self.auth.authenticate()

        # -----------------------------------------
        # Metadata
        # -----------------------------------------

        title = metadata.get(
            "title",
            ""
        ).strip()

        description = metadata.get(
            "description",
            ""
        ).strip()

        tags = metadata.get(
            "tags",
            []
        )

        hashtags = metadata.get(
            "hashtags",
            []
        )

        # Put hashtags at bottom of description
        if hashtags:

            hashtag_text = " ".join(
                hashtags
            )

            description = (
                f"{description}\n\n"
                f"{hashtag_text}"
            )

        # -----------------------------------------
        # YouTube request body
        # -----------------------------------------

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": YOUTUBE_CATEGORY_ID
            },

            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": YOUTUBE_MADE_FOR_KIDS
            }
        }
        # -----------------------------------------
        # Video media
        # -----------------------------------------

        media = MediaFileUpload(
            str(video_path),
            mimetype="video/mp4",
            chunksize=8 * 1024 * 1024,
            resumable=True
        )

        # -----------------------------------------
        # Create upload request
        # -----------------------------------------

        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
            notifySubscribers=YOUTUBE_NOTIFY_SUBSCRIBERS
        )

        print("\n========================================")
        print("UPLOADING VIDEO")
        print("========================================")

        print(f"Title: {title}")
        print(f"Privacy: {privacy_status}")
        print(f"Video: {video_path}")

        response = None

        # -----------------------------------------
        # Resumable upload
        # -----------------------------------------

        while response is None:

            try:

                status, response = (
                    request.next_chunk()
                )

                if status:

                    progress = int(
                        status.progress() * 100
                    )

                    print(
                        f"Upload progress: "
                        f"{progress}%"
                    )

            except HttpError as error:

                print(
                    "\nYouTube upload failed."
                )

                print(error)

                raise

        # -----------------------------------------
        # Get video ID
        # -----------------------------------------

        video_id = response.get("id")

        if not video_id:

            raise RuntimeError(
                "YouTube upload finished, "
                "but no video ID was returned."
            )

        print("\nVideo upload completed!")
        print(f"Video ID: {video_id}")

        # -----------------------------------------
        # Upload thumbnail
        # -----------------------------------------

        thumbnail_uploaded = False

        print("\nUploading custom thumbnail...")

        try:

            thumbnail_media = MediaFileUpload(
                str(thumbnail_path),
                mimetype="image/png"
            )

            youtube.thumbnails().set(
                videoId=video_id,
                media_body=thumbnail_media
            ).execute()

            thumbnail_uploaded = True

            print(
                "Thumbnail uploaded successfully!"
            )

        except HttpError as error:

            # Important:
            # Video already exists at this point.
            print(
                "\nWARNING: Video was uploaded, "
                "but thumbnail upload failed."
            )

            print(error)

        # -----------------------------------------
        # Result
        # -----------------------------------------

        return {
            "video_id": video_id,
            "title": title,
            "privacy_status": privacy_status,
            "thumbnail_uploaded": thumbnail_uploaded
        }