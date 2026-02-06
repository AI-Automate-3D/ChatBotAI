"""Google Docs service.

Mirrors the "Get a document" node in the workflow diagram.
Fetches document content from Google Docs by document ID.
"""

import logging

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

import config

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/documents.readonly"]


class GoogleDocsClient:
    """Fetches plain-text content from Google Docs."""

    def __init__(self) -> None:
        creds = Credentials.from_service_account_file(
            config.GOOGLE_SERVICE_ACCOUNT_FILE,
            scopes=SCOPES,
        )
        self._service = build("docs", "v1", credentials=creds)

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
