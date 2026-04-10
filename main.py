"""
main.py — Principal orchestrator for the Meeting-to-Slides pipeline.

Flow:
  1. Read transcript file (mock Whisper)
  2. Store transcript locally (mock GCS)
  3. Process transcript with Claude API → structured JSON
  4. Create Google Slides presentation
  5. Upload and share via Google Drive
  6. Write cost report to Google Sheets
"""

import sys
import os

from transcriber import transcribe, store_transcript
from ai_processor import process_transcript
from slides_generator import create_presentation
from drive_uploader import upload_and_share
from sheets_reporter import write_report_to_sheets

DEFAULT_TRANSCRIPT = "sample_transcript.txt"
STORED_TRANSCRIPT = os.path.join("outputs", "stored_transcript.txt")


def run_pipeline(transcript_path: str = DEFAULT_TRANSCRIPT) -> None:
    """
    Execute the full meeting-to-slides pipeline end to end.
    Prints progress at each step and a final summary with the shareable link.
    """
    print("=" * 60)
    print("  Meeting-to-Slides Pipeline — POC")
    print("=" * 60)

    # Step 1 — Transcription (mock)
    print("\n[Step 1/6] Transcribing meeting (mock Whisper)...")
    transcript = transcribe(transcript_path)

    # Step 2 — Storage (mock GCS)
    print("\n[Step 2/6] Storing transcript (mock GCS)...")
    store_transcript(transcript, STORED_TRANSCRIPT)

    # Step 3 — AI inference with Claude
    print("\n[Step 3/6] Processing transcript with Claude API...")
    structured_data = process_transcript(transcript)
    print("  Structured data received:")
    print(f"    Summary: {structured_data['executive_summary'][:80]}...")
    print(f"    Objectives: {len(structured_data['objectives'])} items")
    print(f"    Action items: {len(structured_data['action_items'])} items")

    # Step 4 — Create Google Slides presentation
    print("\n[Step 4/6] Creating Google Slides presentation...")
    presentation_id = create_presentation(structured_data)

    # Step 5 — Upload and share via Google Drive
    print("\n[Step 5/6] Uploading and sharing via Google Drive...")
    shareable_link = upload_and_share(presentation_id)

    # Step 6 — Write cost report to Google Sheets
    print("\n[Step 6/6] Writing cost report to Google Sheets...")
    write_report_to_sheets()

    # Final summary
    print("\n" + "=" * 60)
    print("  Pipeline completed successfully!")
    print(f"  Presentation ID : {presentation_id}")
    print(f"  Shareable link  : {shareable_link}")
    print(f"  Cost report     : outputs/cost_report.json")
    print("=" * 60)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TRANSCRIPT
    try:
        run_pipeline(path)
    except (FileNotFoundError, EnvironmentError, PermissionError, RuntimeError, ValueError) as e:
        print(f"\n[ERROR] Pipeline failed: {e}", file=sys.stderr)
        sys.exit(1)
