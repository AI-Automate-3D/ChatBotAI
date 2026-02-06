"""Google Docs service.

Mirrors the "Get a document" node in the workflow diagram.
Fetches document content from Google Docs by document ID.

Uses OAuth2 (client ID + secret) — on first run it opens a browser
for you to authorize, then saves the token for future use.
"""

import json
import logging
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import config

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/documents.readonly"]


class GoogleDocsClient:
    """Fetches plain-text content from Google Docs via OAuth2."""

    def __init__(self) -> None:
        creds = self._get_credentials()
        self._service = build("docs", "v1", credentials=creds)

    @staticmethod
    def _get_credentials() -> Credentials:
        """Load saved token or run the OAuth2 flow to create one."""
        token_path = Path(config.GOOGLE_TOKEN_FILE)
        creds = None

        # Try loading an existing token
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

        # Refresh or re-authenticate
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired Google token …")
            creds.refresh(Request())
        elif not creds or not creds.valid:
            logger.info("Starting Google OAuth2 authorization flow …")
            client_config = {
                "installed": {
                    "client_id": config.GOOGLE_CLIENT_ID,
                    "client_secret": config.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["http://localhost"],
                }
            }
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=0)

            # Save the token for next time
            token_path.parent.mkdir(parents=True, exist_ok=True)
            token_path.write_text(creds.to_json())
            logger.info("Google token saved to %s", token_path)

        return creds

    def get_document_text(self, document_id: str) -> str:
        """Fetch a Google Doc by *document_id* and return its plain text."""
        doc = self._service.documents().get(documentId=document_id).execute()
        title = doc.get("title", "")
        body = doc.get("body", {})
        text = self._extract_text(body)
        logger.info("Fetched Google Doc '%s' (%d chars)", title, len(text))
        return text

    @staticmethod
    def _extract_text(body: dict) -> str:
        """Walk the document body and concatenate all text runs."""
        parts: list[str] = []
        for element in body.get("content", []):
            paragraph = element.get("paragraph")
            if not paragraph:
                continue
            for run in paragraph.get("elements", []):
                text_run = run.get("textRun")
                if text_run:
                    parts.append(text_run.get("content", ""))
        return "".join(parts)
