"""
sheets_reporter.py — Calls the Google Sheets API to write the cost report
from outputs/cost_report.json into a designated Google Sheets spreadsheet.
"""

import json
import os
from datetime import datetime

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
COST_REPORT_PATH = os.path.join("outputs", "cost_report.json")
SHEET_NAME = "CostReport"


def _get_sheets_service():
    """Build and return an authenticated Google Sheets API service client."""
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
        service = build("sheets", "v4", credentials=creds)
    except Exception as e:
        raise RuntimeError(f"Failed to build Google Sheets service: {e}") from e

    return service


def _load_cost_report() -> list:
    """Load and return all entries from outputs/cost_report.json."""
    if not os.path.exists(COST_REPORT_PATH):
        raise FileNotFoundError(
            f"Cost report not found at: {COST_REPORT_PATH}. "
            "Run the pipeline first to generate it."
        )

    try:
        with open(COST_REPORT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        raise ValueError(f"Failed to parse cost report JSON: {e}") from e

    return data if isinstance(data, list) else [data]


def _build_rows(entries: list) -> list:
    """Convert cost report entries into a list of rows for Sheets (header + data rows)."""
    header = ["Step", "Model", "Input Tokens", "Output Tokens", "Cost (USD)", "Timestamp"]
    rows = [header]
    for entry in entries:
        rows.append([
            entry.get("step", ""),
            entry.get("model", ""),
            entry.get("input_tokens", 0),
            entry.get("output_tokens", 0),
            entry.get("cost_usd", 0.0),
            entry.get("timestamp", ""),
        ])
    return rows


def write_report_to_sheets() -> None:
    """
    Full pipeline: load cost_report.json, build rows, and append them to the
    configured Google Sheets spreadsheet. Adds a header row on first write.
    """
    spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
    if not spreadsheet_id:
        raise EnvironmentError(
            "GOOGLE_SHEETS_SPREADSHEET_ID not set in environment. Check your .env file."
        )

    service = _get_sheets_service()
    entries = _load_cost_report()
    rows = _build_rows(entries)

    range_notation = f"{SHEET_NAME}!A1"

    try:
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_notation,
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": rows},
        ).execute()
    except HttpError as e:
        raise RuntimeError(
            f"Google Sheets API error writing report to spreadsheet '{spreadsheet_id}': {e}"
        ) from e

    print(f"Cost report written to Google Sheets spreadsheet: {spreadsheet_id}")
    print(f"  Rows written: {len(rows) - 1} (plus header)")
