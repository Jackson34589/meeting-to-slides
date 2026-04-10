"""
slides_generator.py — Calls the Google Slides API to create a presentation
from the structured JSON output produced by ai_processor.py.
"""

import os

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/presentations"]


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
    """
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
