import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from google.auth.exceptions import RefreshError

from youtube_engine import youtube_auth
from youtube_engine.youtube_auth import (
    YouTubeAuth,
    YouTubeAuthenticationError
)


class FakeCredentials:
    def __init__(
        self,
        *,
        valid,
        expired=False,
        refresh_token=None,
        refresh_error=None,
        json_text='{"token": "new"}'
    ):
        self.valid = valid
        self.expired = expired
        self.refresh_token = refresh_token
        self.refresh_error = refresh_error
        self.json_text = json_text
        self.refresh_calls = 0

    def refresh(self, request):
        self.refresh_calls += 1
        if self.refresh_error is not None:
            raise self.refresh_error
        self.valid = True
        self.expired = False

    def to_json(self):
        return self.json_text


class YouTubeAuthRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary_directory.name)
        self.token_path = self.directory / "youtube_token.json"
        self.client_path = self.directory / "youtube_client_secret.json"
        self.client_path.write_text("client credentials", encoding="utf-8")
        self.service = object()

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _auth(self):
        auth = YouTubeAuth()
        auth.token_path = self.token_path
        auth.client_secret_path = self.client_path
        return auth

    def _authenticate(self, cached, authorized=None):
        self.token_path.write_text("cached token", encoding="utf-8")
        flow = Mock()
        flow.run_local_server.return_value = authorized

        patches = (
            patch.object(
                youtube_auth.Credentials,
                "from_authorized_user_file",
                return_value=cached
            ),
            patch.object(
                youtube_auth.InstalledAppFlow,
                "from_client_secrets_file",
                return_value=flow
            ),
            patch.object(
                youtube_auth,
                "build",
                return_value=self.service
            )
        )

        return flow, patches

    def test_valid_cached_credentials_work_normally(self):
        cached = FakeCredentials(valid=True)
        flow, patches = self._authenticate(cached)

        with patches[0], patches[1] as create_flow, patches[2]:
            result = self._auth().authenticate()

        self.assertIs(result, self.service)
        self.assertEqual(cached.refresh_calls, 0)
        create_flow.assert_not_called()

    def test_expired_access_token_refreshes_normally(self):
        cached = FakeCredentials(
            valid=False,
            expired=True,
            refresh_token="available",
            json_text='{"token": "refreshed"}'
        )
        flow, patches = self._authenticate(cached)

        with patches[0], patches[1] as create_flow, patches[2]:
            result = self._auth().authenticate()

        self.assertIs(result, self.service)
        self.assertEqual(cached.refresh_calls, 1)
        create_flow.assert_not_called()
        self.assertEqual(
            self.token_path.read_text(encoding="utf-8"),
            cached.json_text
        )

    def test_invalid_grant_removes_stale_token_and_reauthorizes_once(self):
        cached = FakeCredentials(
            valid=False,
            expired=True,
            refresh_token="revoked",
            refresh_error=RefreshError(
                "invalid_grant: Token has been expired or revoked."
            )
        )
        authorized = FakeCredentials(
            valid=True,
            json_text='{"token": "reauthorized"}'
        )
        flow, patches = self._authenticate(cached, authorized)

        def authorize_once(port):
            self.assertEqual(port, 0)
            self.assertFalse(self.token_path.exists())
            return authorized

        flow.run_local_server.side_effect = authorize_once

        with patches[0], patches[1] as create_flow, patches[2]:
            result = self._auth().authenticate()

        self.assertIs(result, self.service)
        self.assertEqual(cached.refresh_calls, 1)
        create_flow.assert_called_once()
        flow.run_local_server.assert_called_once_with(port=0)
        self.assertTrue(self.client_path.is_file())

    def test_newly_authorized_credentials_are_saved(self):
        cached = FakeCredentials(
            valid=False,
            expired=True,
            refresh_token="revoked",
            refresh_error=RefreshError("invalid_grant")
        )
        authorized = FakeCredentials(
            valid=True,
            json_text='{"token": "new authorization"}'
        )
        flow, patches = self._authenticate(cached, authorized)

        with patches[0], patches[1], patches[2]:
            self._auth().authenticate()

        self.assertEqual(
            self.token_path.read_text(encoding="utf-8"),
            authorized.json_text
        )
        self.assertNotEqual(
            self.token_path.read_text(encoding="utf-8"),
            "cached token"
        )

    def test_unrelated_refresh_error_is_controlled(self):
        cached = FakeCredentials(
            valid=False,
            expired=True,
            refresh_token="available",
            refresh_error=RefreshError(
                "temporarily_unavailable: OAuth server error"
            )
        )
        flow, patches = self._authenticate(cached)

        with patches[0], patches[1] as create_flow, patches[2]:
            with self.assertRaisesRegex(
                YouTubeAuthenticationError,
                "Could not refresh"
            ):
                self._auth().authenticate()

        create_flow.assert_not_called()
        self.assertEqual(
            self.token_path.read_text(encoding="utf-8"),
            "cached token"
        )


if __name__ == "__main__":
    unittest.main()
