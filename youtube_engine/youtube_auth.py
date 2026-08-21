from pathlib import Path

from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import (
    YOUTUBE_CLIENT_SECRET_PATH,
    YOUTUBE_TOKEN_PATH,
)


class YouTubeAuthenticationError(RuntimeError):
    """Raised when YouTube authentication cannot be completed."""


class YouTubeAuth:

    SCOPES = [
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube.readonly",
    ]

    def __init__(self):

        self.client_secret_path = Path(
            YOUTUBE_CLIENT_SECRET_PATH
        )

        self.token_path = Path(
            YOUTUBE_TOKEN_PATH
        )

    def authenticate(self):

        credentials = None

        # -----------------------------------------
        # Load existing token
        # -----------------------------------------

        if self.token_path.exists():

            credentials = Credentials.from_authorized_user_file(
                str(self.token_path),
                self.SCOPES
            )

        # -----------------------------------------
        # Refresh or login
        # -----------------------------------------

        if not credentials or not credentials.valid:

            if (
                credentials
                and credentials.expired
                and credentials.refresh_token
            ):

                print("Refreshing YouTube login...")

                try:
                    credentials.refresh(
                        Request()
                    )
                except RefreshError as error:
                    if not self._is_invalid_grant(error):
                        raise YouTubeAuthenticationError(
                            "Could not refresh the saved YouTube "
                            "login. Please try again later."
                        ) from error

                    print(
                        "Saved YouTube login expired or was revoked."
                    )
                    print(
                        "Starting YouTube authorization again..."
                    )

                    self.token_path.unlink(
                        missing_ok=True
                    )

                    credentials = self._authorize()

            else:
                credentials = self._authorize()

            # -------------------------------------
            # Save token
            # -------------------------------------

            self.token_path.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            self.token_path.write_text(
                credentials.to_json(),
                encoding="utf-8"
            )

            print(
                f"YouTube token saved: "
                f"{self.token_path}"
            )

        # -----------------------------------------
        # Build YouTube API client
        # -----------------------------------------

        youtube = build(
            "youtube",
            "v3",
            credentials=credentials
        )

        return youtube

    def _authorize(self):

        if not self.client_secret_path.exists():
            raise FileNotFoundError(
                "YouTube OAuth credentials not found:\n"
                f"{self.client_secret_path}"
            )

        print(
            "Opening browser for YouTube authorization..."
        )

        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(self.client_secret_path),
                self.SCOPES
            )

            return flow.run_local_server(
                port=0
            )
        except Exception as error:
            raise YouTubeAuthenticationError(
                "YouTube authorization did not complete. "
                "Please try Stage 6 again."
            ) from error

    @staticmethod
    def _is_invalid_grant(error):

        text = " ".join(
            str(value)
            for value in (
                error,
                getattr(error, "args", None)
            )
            if value is not None
        ).lower()

        return (
            "invalid_grant" in text
            or "token has been expired or revoked" in text
        )
