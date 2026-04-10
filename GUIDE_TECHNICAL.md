# Meeting to Slides — Technical Guide

## System Architecture

```
[.txt transcript]
      |
      v
transcriber.py       <- Reads the file (mock Whisper / real Whisper API)
      |
      v
outputs/stored_transcript.txt   <- Local storage (mock GCS)
      |
      v
ai_processor.py      <- Calls Claude API -> returns structured JSON
      |                  Logs tokens and cost via cost_tracker.py
      v
slides_generator.py  <- Creates presentation via Google Slides API
      |
      v
drive_uploader.py    <- Moves file and creates public permission via Drive API
      |
      v
sheets_reporter.py   <- Writes cost report via Sheets API
      |
      v
outputs/cost_report.json  <- Cumulative log of each API call
```

### Module responsibilities

| File | Single responsibility |
|---|---|
| `main.py` | Orchestrator — runs the 6 steps in sequence |
| `transcriber.py` | Read transcript from disk; mock for Whisper and GCS |
| `ai_processor.py` | Claude API call; mock fallback; JSON validation |
| `slides_generator.py` | Presentation creation via Slides API; mock fallback |
| `drive_uploader.py` | Upload and permissions via Drive API; mock fallback |
| `sheets_reporter.py` | Report writing via Sheets API; mock fallback |
| `cost_tracker.py` | Cost calculation, JSON write, console output |

---

## Environment Setup

### Requirements

- Python 3.11+
- Anthropic account with an active API key
- Google Cloud project with the following APIs enabled:
  - Google Slides API
  - Google Drive API
  - Google Sheets API
- GCP service account with roles: Editor on Drive, Slides, and Sheets

### Installation

```bash
git clone https://github.com/Jackson34589/meeting-to-slides.git
cd meeting-to-slides
pip install -r requirements.txt
```

### Environment variables (`.env`)

```env
# Required for AI inference
ANTHROPIC_API_KEY=sk-ant-api03-...

# Path to Google Cloud service account JSON
GOOGLE_CREDENTIALS_PATH=credentials.json

# Google resource IDs
GOOGLE_SLIDES_FOLDER_ID=1ABC...     # Folder where the presentation is created
GOOGLE_DRIVE_FOLDER_ID=1XYZ...      # Destination folder for the final file
GOOGLE_SHEETS_SPREADSHEET_ID=1DEF...# Cost spreadsheet ID

# Mocked in this POC — not used in current production
WHISPER_API_KEY=your_key_here
GCS_BUCKET_NAME=your_bucket
```

> **Security:** `.env` and `credentials.json` are in `.gitignore`. Never commit them to the repository.

### Getting `credentials.json`

1. Go to [Google Cloud Console](https://console.cloud.google.com) > IAM & Admin > Service Accounts
2. Create a service account or select an existing one
3. Go to the **Keys** tab > **Add Key** > **JSON**
4. Download the file and rename it `credentials.json` in the project root
5. Share the Drive folders and the spreadsheet with the service account email

---

## Mock mode (development without credentials)

All integration modules automatically detect if the credentials are placeholders and run mocks instead. No special flag is required.

### Detection logic

**Claude API (`ai_processor.py`)**
```python
_PLACEHOLDER_KEYS = {"your_key_here", "", "your-api-key", "sk-ant-placeholder"}

def _is_placeholder(api_key: str) -> bool:
    return not api_key or api_key.strip() in _PLACEHOLDER_KEYS
```

**Google APIs (`slides_generator.py`, `drive_uploader.py`, `sheets_reporter.py`)**
```python
_PLACEHOLDER_PATHS = {"credentials.json", "your_credentials.json", ""}

def _credentials_available() -> bool:
    path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    return path not in _PLACEHOLDER_PATHS and os.path.exists(path)
```

### Mock behavior per module

| Module | What it simulates | Visible output |
|---|---|---|
| `ai_processor` | Claude response | JSON with summary, objectives, action items derived from the transcript |
| `slides_generator` | Presentation creation | Random presentation ID (UUID), content of each slide |
| `drive_uploader` | Upload + share | Link with real format `https://docs.google.com/presentation/d/{id}/edit?usp=sharing` |
| `sheets_reporter` | Sheets write | Formatted table with the rows that would have been written |

To activate the real APIs:
1. Place a valid `credentials.json` in the project root
2. Update `GOOGLE_CREDENTIALS_PATH` in `.env` if the file has a different name
3. Set the real `ANTHROPIC_API_KEY` in `.env`

---

## Cost Tracking

### `outputs/cost_report.json` structure

```json
[
  {
    "step": "summarization",
    "model": "claude-sonnet-4-6",
    "input_tokens": 1726,
    "output_tokens": 180,
    "cost_usd": 0.007878,
    "timestamp": "2026-04-10T17:00:00Z"
  }
]
```

The file is a cumulative array — each run appends a new entry. It is never overwritten.

### Cost formula (`cost_tracker.py`)

```python
INPUT_PRICE_PER_MILLION  = 3.00   # USD per million input tokens
OUTPUT_PRICE_PER_MILLION = 15.00  # USD per million output tokens

cost = (input_tokens / 1_000_000 * 3.00) + (output_tokens / 1_000_000 * 15.00)
```

### Projected monthly cost

| Item | Value |
|---|---|
| Input tokens per meeting | ~12,000 (60-min transcript) |
| Output tokens per meeting | ~800 (structured JSON) |
| Cost per meeting | ~$0.048 USD |
| Meetings per month (estimate) | 20 |
| **Monthly AI cost** | **~$0.96 USD** |

---

## Troubleshooting

### Error: `ANTHROPIC_API_KEY not found` or `authentication_error`
- Verify that `.env` exists in the project root
- Confirm the key starts with `sk-ant-`
- Make sure `load_dotenv()` is called before `os.getenv()`

### Error: `Google credentials file not found`
- Verify that `credentials.json` exists at the path specified in `GOOGLE_CREDENTIALS_PATH`
- Confirm the file is a valid service account JSON (has fields `type`, `project_id`, `private_key`)

### Error: `HttpError 403` on Google APIs
- The service account does not have permissions on the resource
- Share the Drive folder or spreadsheet directly with the service account email (visible in `credentials.json` as `client_email`)

### Error: `Claude returned invalid JSON`
- Rare with `claude-sonnet-4-6`, but can occur if the transcript contains special characters that confuse the prompt
- Check the transcript for code blocks or unusual symbols
- The `SYSTEM_PROMPT` in `ai_processor.py` can be reinforced with additional instructions

### Error: `cost_report.json` is not generated
- Confirm the `outputs/` folder exists (created automatically, but may fail if there are no write permissions)
- Verify that `cost_tracker.save_entry()` is not being skipped in the flow

### Pipeline fails at Step 4 but Steps 1-3 pass
- This is the expected behavior when `credentials.json` does not exist and `_credentials_available()` returns `False` for some unexpected reason
- Check the `_credentials_available()` logs to confirm the path being evaluated

---

## Monitoring and Logging Recommendations

### Current logs
All steps print to `stdout` with clear prefixes:
- `[MOCK]` — simulated call, not real
- `[Step N/6]` — pipeline progress
- `=== COST SUMMARY ===` — cost summary per call

### For production it is recommended to

**1. Replace `print` with a structured logger**
```python
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)
# Replace print(...) with logger.info(...) / logger.error(...)
```

**2. Cost alerts**
Add a check in `cost_tracker.py` that sends an alert if the accumulated monthly cost exceeds a threshold:
```python
MONTHLY_BUDGET_USD = 5.00  # Adjust as needed
```

**3. `cost_report.json` rotation**
In production with high volume, consider rotating the file monthly or migrating to a lightweight database (SQLite).

**4. Retries with backoff**
Add automatic retries on Claude and Google API calls using `tenacity`:
```bash
pip install tenacity
```
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _call_claude_with_retry(client, **kwargs):
    return client.messages.create(**kwargs)
```

**5. Environment separation**
Use `.env.development` and `.env.production` files with the `python-dotenv` library:
```python
load_dotenv(".env.production")  # In the production orchestrator
```

---

## Future Extensions (out of POC scope)

| Extension | Description |
|---|---|
| Real Whisper | Replace `transcriber.py` mock with a real call to `openai.Audio.transcribe()` |
| Real GCS | Replace local storage with `google-cloud-storage` |
| Multiple Claude calls | Split the transcript into chunks for meetings longer than 2 hours |
| Slide templates | Apply corporate branding using `requests` on the Slides API |
| Webhook / trigger | Expose `main.py` as an HTTP endpoint with FastAPI to integrate with Zapier or Make |
| Automated tests | Add `pytest` with fixtures that use the existing mocks |
