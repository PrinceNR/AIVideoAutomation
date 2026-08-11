from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


class YouTubeAuth:

    SCOPES = [
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube.readonly",
    ]

    def __init__(self):

        self.client_secret_path = Path(
            "credentials/youtube_client_secret.json"
        )

        self.token_path = Path(
            "credentials/youtube_token.json"
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

                credentials.refresh(
                    Request()
                )

            else:

                if not self.client_secret_path.exists():

                    raise FileNotFoundError(
                        "YouTube OAuth credentials not found:\n"
                        f"{self.client_secret_path}"
                    )

                print(
                    "Opening browser for YouTube authorization..."
                )

                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.client_secret_path),
                    self.SCOPES
                )

                credentials = flow.run_local_server(
                    port=0
                )

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