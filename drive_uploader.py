"""
drive_uploader.py — Calls the Google Drive API to upload the presentation
to a specified folder and share it (make it readable by anyone with the link).
Falls back to a mock response when Google credentials are unavailable.
"""

import os

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/drive"]
_PLACEHOLDER_PATHS = {"credentials.json", "your_credentials.json", ""}


def _credentials_available() -> bool:
    """Return True if a real Google credentials file exists on disk."""
    path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    return path not in _PLACEHOLDER_PATHS and os.path.exists(path)


def _mock_upload_and_share(presentation_id: str) -> str:
    """
    Simulate a successful Google Drive upload and share without real credentials.
    Returns a realistic-format (but non-functional) Google Slides shareable link.
    """
    mock_link = f"https://docs.google.com/presentation/d/{presentation_id}/edit?usp=sharing"
    folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "your_drive_folder_id")

    print("[MOCK] Google Drive API call skipped — simulating upload and share.")
    print(f"[MOCK] Presentation ID : {presentation_id}")
    print(f"[MOCK] Target folder   : {folder_id}")
    print(f"[MOCK] Permissions set : anyone with link -> viewer")
    print(f"[MOCK] Shareable link  : {mock_link}")
    return mock_link


def _get_drive_service():
    """Build and return an authenticated Google Drive API service client."""
    credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")

    if not os.path.exists(credentials_path):
        raise FileNotFoundError(
            f"Google credentials file not found at: {credentials_path}. "
            "Set GOOGLE_CREDENTIALS_PATH in your .env file."
        )

    try:
        creds = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=SCOPES
        )
        service = build("drive", "v3", credentials=creds)
    except Exception as e:
        raise RuntimeError(f"Failed to build Google Drive service: {e}") from e

    return service


def move_to_folder(presentation_id: str, folder_id: str) -> None:
    """
    Move an existing Google Slides file (by presentation_id) into the specified Drive folder.
    Uses Drive API file.update to add the parent folder.
    """
    service = _get_drive_service()

    try:
        file = service.files().get(
            fileId=presentation_id, fields="parents"
        ).execute()
        previous_parents = ",".join(file.get("parents", []))

        service.files().update(
            fileId=presentation_id,
            addParents=folder_id,
            removeParents=previous_parents,
            fields="id, parents",
        ).execute()
    except HttpError as e:
        raise RuntimeError(
            f"Google Drive API error moving file '{presentation_id}' to folder '{folder_id}': {e}"
        ) from e

    print(f"Presentation moved to Drive folder: {folder_id}")


def share_publicly(presentation_id: str) -> str:
    """
    Share the presentation so anyone with the link can view it.
    Returns the shareable link URL.
    """
    service = _get_drive_service()

    permission = {"type": "anyone", "role": "reader"}

    try:
        service.permissions().create(
            fileId=presentation_id,
            body=permission,
            fields="id",
        ).execute()

        file_meta = service.files().get(
            fileId=presentation_id, fields="webViewLink"
        ).execute()
    except HttpError as e:
        raise RuntimeError(
            f"Google Drive API error sharing file '{presentation_id}': {e}"
        ) from e

    link = file_meta.get("webViewLink", "")
    print(f"Presentation shared publicly. Link: {link}")
    return link


def upload_and_share(presentation_id: str) -> str:
    """
    Full pipeline: move the presentation to the configured Drive folder and make it publicly readable.
    Returns the shareable link. Falls back to a mock if credentials are unavailable.
    """
    if not _credentials_available():
        return _mock_upload_and_share(presentation_id)

    folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
    if not folder_id:
        raise EnvironmentError(
            "GOOGLE_DRIVE_FOLDER_ID not set in environment. Check your .env file."
        )

    move_to_folder(presentation_id, folder_id)
    link = share_publicly(presentation_id)
    return link
