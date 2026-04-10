"""
slides_generator.py — Calls the Google Slides API to create a presentation
from the structured JSON output produced by ai_processor.py.
Falls back to a mock response when Google credentials are unavailable.
"""

import os
import uuid

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/presentations"]
_PLACEHOLDER_PATHS = {"credentials.json", "your_credentials.json", ""}


def _credentials_available() -> bool:
    """Return True if a real Google credentials file exists on disk."""
    path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    return path not in _PLACEHOLDER_PATHS and os.path.exists(path)


def _mock_create_presentation(structured_data: dict, title: str) -> str:
    """
    Simulate a successful Google Slides API call without real credentials.
    Generates a realistic presentation ID and prints a summary of the slides content.
    """
    presentation_id = uuid.uuid4().hex[:44].upper()
    # Pad to match real Google Slides ID length (~44 alphanumeric chars)
    presentation_id = (presentation_id + uuid.uuid4().hex)[:44]

    print("[MOCK] Google Slides API call skipped — simulating presentation creation.")
    print(f"[MOCK] Title     : {title}")
    print(f"[MOCK] Slides    : 5 (Title, Executive Summary, Objectives, Action Items, Next Steps)")
    print(f"[MOCK] Slide 1 — Title: {title}")
    print(f"[MOCK] Slide 2 — Executive Summary: {structured_data.get('executive_summary', '')[:80]}...")
    print(f"[MOCK] Slide 3 — Objectives ({len(structured_data.get('objectives', []))} items):")
    for obj in structured_data.get("objectives", []):
        print(f"         * {obj}")
    print(f"[MOCK] Slide 4 — Action Items ({len(structured_data.get('action_items', []))} items):")
    for item in structured_data.get("action_items", []):
        print(f"         * {item}")
    print(f"[MOCK] Slide 5 — Next Steps: {structured_data.get('next_steps', '')[:80]}...")
    print(f"[MOCK] Presentation ID: {presentation_id}")
    return presentation_id


def _get_slides_service():
    """Build and return an authenticated Google Slides API service client."""
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
        service = build("slides", "v1", credentials=creds)
    except Exception as e:
        raise RuntimeError(f"Failed to build Google Slides service: {e}") from e

    return service


def create_presentation(structured_data: dict, title: str = "Meeting Summary") -> str:
    """
    Create a Google Slides presentation from structured meeting data.
    Returns the presentation ID of the newly created file.
    Falls back to a mock if Google credentials are unavailable.
    """
    if not _credentials_available():
        return _mock_create_presentation(structured_data, title)

    service = _get_slides_service()

    try:
        presentation = service.presentations().create(
            body={"title": title}
        ).execute()
    except HttpError as e:
        raise RuntimeError(f"Google Slides API error creating presentation: {e}") from e

    presentation_id = presentation["presentationId"]
    print(f"Presentation created with ID: {presentation_id}")

    requests = _build_slide_requests(presentation, structured_data)

    if requests:
        try:
            service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={"requests": requests},
            ).execute()
        except HttpError as e:
            raise RuntimeError(f"Google Slides API error updating slides: {e}") from e

    print(f"Slides populated successfully for presentation: {presentation_id}")
    return presentation_id


def _build_slide_requests(presentation: dict, data: dict) -> list:
    """
    Build the list of batchUpdate requests to populate the presentation with content.
    Covers: title slide, executive summary, objectives, action items, next steps.
    """
    requests = []
    existing_slide_id = presentation["slides"][0]["objectId"]

    # Slide 1 — Title (reuse the default blank slide)
    title_id = f"{existing_slide_id}_title"
    subtitle_id = f"{existing_slide_id}_subtitle"

    requests += [
        {
            "insertText": {
                "objectId": existing_slide_id,
                "insertionIndex": 0,
                "text": "Meeting Summary",
            }
        }
    ]

    # Slides 2-4 — Add new slides for each section
    sections = [
        ("Executive Summary", data.get("executive_summary", "")),
        (
            "High-Level Objectives",
            "\n".join(f"• {o}" for o in data.get("objectives", [])),
        ),
        (
            "Action Items",
            "\n".join(f"• {a}" for a in data.get("action_items", [])),
        ),
        ("Next Steps", data.get("next_steps", "")),
    ]

    for section_title, section_body in sections:
        new_slide_id = f"slide_{section_title.replace(' ', '_').lower()}"
        title_shape_id = f"{new_slide_id}_title"
        body_shape_id = f"{new_slide_id}_body"

        requests += [
            {
                "addSlide": {
                    "objectId": new_slide_id,
                    "slideLayoutReference": {"predefinedLayout": "TITLE_AND_BODY"},
                    "placeholderIdMappings": [
                        {
                            "layoutPlaceholder": {
                                "type": "TITLE",
                                "index": 0,
                            },
                            "objectId": title_shape_id,
                        },
                        {
                            "layoutPlaceholder": {
                                "type": "BODY",
                                "index": 0,
                            },
                            "objectId": body_shape_id,
                        },
                    ],
                }
            },
            {
                "insertText": {
                    "objectId": title_shape_id,
                    "insertionIndex": 0,
                    "text": section_title,
                }
            },
            {
                "insertText": {
                    "objectId": body_shape_id,
                    "insertionIndex": 0,
                    "text": section_body,
                }
            },
        ]

    return requests
