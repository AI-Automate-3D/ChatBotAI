"""Gmail OAuth2 authentication — build an authenticated Gmail API service.

Handles the full OAuth2 flow: load credentials, refresh tokens, and
construct a ``googleapiclient.discovery.Resource`` object ready for use.

Designed to be reusable — no pipeline-specific logic.

Usage
-----
    from gmail.utils.auth import get_gmail_service

    # Uses default config paths
    service = get_gmail_service()

    # Or provide explicit paths
    service = get_gmail_service(
        credentials_path="credentials/gmail-credentials.json",
        token_path="credentials/gmail-token.json",
    )
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource

logger = logging.getLogger(__name__)

# Gmail API scopes — full access to read, send, modify, and manage mail.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.labels",
]

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_CREDENTIALS = _PROJECT_ROOT / "credentials" / "gmail-credentials.json"
_DEFAULT_TOKEN = _PROJECT_ROOT / "credentials" / "gmail-token.json"


def _load_config_paths() -> tuple[Path, Path]:
    """Attempt to read credential paths from config.json.

    Falls back to the defaults in ``credentials/`` if config.json
    doesn't exist or doesn't contain Gmail settings.
    """
    config_path = _PROJECT_ROOT / "_config files" / "config.json"
    if not config_path.exists():
        return _DEFAULT_CREDENTIALS, _DEFAULT_TOKEN

    try:
        cfg = json.loads(config_path.read_text(encoding="utf-8"))
        gmail_cfg = cfg.get("gmail", {})
        creds = gmail_cfg.get("credentials_file", str(_DEFAULT_CREDENTIALS))
        token = gmail_cfg.get("token_file", str(_DEFAULT_TOKEN))
        return Path(creds), Path(token)
    except (json.JSONDecodeError, OSError):
        return _DEFAULT_CREDENTIALS, _DEFAULT_TOKEN


def authenticate(
    credentials_path: str | Path | None = None,
    token_path: str | Path | None = None,
    scopes: list[str] | None = None,
) -> Credentials:
    """Authenticate with Google and return valid credentials.

    On first run, opens a browser for the OAuth consent flow and saves
    the resulting token.  On subsequent runs, loads and refreshes the
    stored token automatically.

    Parameters
    ----------
    credentials_path : str | Path | None
        Path to the OAuth2 client secrets JSON (downloaded from Google
        Cloud Console).  Defaults to ``credentials/gmail-credentials.json``.
    token_path : str | Path | None
        Path where the access/refresh token will be stored.
        Defaults to ``credentials/gmail-token.json``.
    scopes : list[str] | None
        OAuth2 scopes.  Defaults to read + send + modify + labels.

    Returns
    -------
    google.oauth2.credentials.Credentials
        Authenticated credentials ready for API calls.

    Raises
    ------
    SystemExit
        If the credentials file does not exist.
    """
    default_creds, default_token = _load_config_paths()
    creds_path = Path(credentials_path) if credentials_path else default_creds
    tok_path = Path(token_path) if token_path else default_token
    scopes = scopes or SCOPES

    creds: Credentials | None = None

    # Load existing token
    if tok_path.exists():
        creds = Credentials.from_authorized_user_file(str(tok_path), scopes)

    # Refresh or run the OAuth flow
    if creds and creds.valid:
        logger.debug("Using cached Gmail token")
    elif creds and creds.expired and creds.refresh_token:
        logger.info("Refreshing expired Gmail token")
        creds.refresh(Request())
    else:
        if not creds_path.exists():
            sys.exit(
                f"ERROR: Gmail credentials file not found: {creds_path}\n"
                "Download OAuth2 client secrets from Google Cloud Console\n"
                "and save them as credentials/gmail-credentials.json."
            )
        logger.info("Running OAuth2 flow — a browser window will open")
        flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), scopes)
        creds = flow.run_local_server(port=0)

    # Persist the token
    tok_path.parent.mkdir(parents=True, exist_ok=True)
    tok_path.write_text(creds.to_json(), encoding="utf-8")
    logger.info("Gmail token saved to %s", tok_path)

    return creds


def get_gmail_service(
    credentials_path: str | Path | None = None,
    token_path: str | Path | None = None,
    scopes: list[str] | None = None,
) -> Resource:
    """Return an authenticated Gmail API service object.

    Parameters
    ----------
    credentials_path : str | Path | None
        Path to OAuth2 client secrets JSON.
    token_path : str | Path | None
        Path to cached token JSON.
    scopes : list[str] | None
        OAuth2 scopes.

    Returns
    -------
    googleapiclient.discovery.Resource
        Authenticated Gmail API v1 service.
    """
    creds = authenticate(credentials_path, token_path, scopes)
    service = build("gmail", "v1", credentials=creds)
    logger.info("Gmail API service ready")
    return service
