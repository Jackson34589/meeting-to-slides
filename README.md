# Meeting to Slides — AI Automation Pipeline

Automated workflow that ingests a meeting transcript, processes it with the Claude API, and delivers a fully structured Google Slides presentation — with cost tracking included.

---

## What it does

Given a plain-text meeting transcript, the pipeline:

1. Reads the transcript (simulating Whisper output)
2. Stores it locally (simulating Google Cloud Storage)
3. Sends it to Claude (`claude-sonnet-4-6`) → returns structured JSON
4. Creates a Google Slides presentation with the extracted content
5. Uploads and shares the file via Google Drive
6. Writes a cost report to Google Sheets
7. Prints a cost summary to the console

### Generated slide content

- Executive summary
- 3 high-level objectives
- 3 actionable items with owners
- Next steps

---

## Architecture

```
[Transcript .txt] → [Transcriber (mock Whisper)] → [Storage (local/mock GCS)]
      → [Claude API] → [Content Formatter] → [Google Slides API] → [Presentation]
                                           ↘ [Google Drive API]  → [Stores & shares file]
                                           ↘ [Google Sheets API] → [Cost report spreadsheet]
```

---

## Project structure

```
meeting-to-slides/
├── main.py                  # Pipeline orchestrator
├── transcriber.py           # Mock transcriber (simulates Whisper API)
├── ai_processor.py          # Claude API integration + token/cost tracking
├── slides_generator.py      # Google Slides API — creates the presentation
├── drive_uploader.py        # Google Drive API — uploads and shares the file
├── sheets_reporter.py       # Google Sheets API — writes the cost report
├── cost_tracker.py          # Logs cost per API call to cost_report.json
├── sample_transcript.txt    # Sample transcript for local testing
├── requirements.txt
├── .env                     # API keys (never committed)
└── outputs/
    └── cost_report.json     # Auto-generated cost report
```

---

## Tech stack

| Component | Tool |
|---|---|
| Language | Python 3.11+ |
| AI inference | Claude API (`claude-sonnet-4-6`) |
| Transcription | OpenAI Whisper API (mocked) |
| Presentation | Google Slides API |
| File storage | Google Drive API |
| Cost report | Google Sheets API |
| Env vars | python-dotenv |
| Cost tracking | Custom (`cost_tracker.py`) |

---

## Setup

### 1. Clone and install dependencies

```bash
git clone https://github.com/your-username/meeting-to-slides.git
cd meeting-to-slides
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy `.env.example` to `.env` and fill in your credentials:

```env
ANTHROPIC_API_KEY=your_key_here
GOOGLE_CREDENTIALS_PATH=credentials.json
GOOGLE_SLIDES_FOLDER_ID=your_folder_id
GOOGLE_DRIVE_FOLDER_ID=your_drive_folder_id
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id
```

> `.env` is gitignored. Never commit API keys.

### 3. Google API credentials

- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Enable the **Slides**, **Drive**, and **Sheets** APIs
- Create a Service Account and download `credentials.json`
- Place `credentials.json` in the project root

### 4. Run the pipeline

```bash
# Using the sample transcript
python main.py

# Using a custom transcript
python main.py path/to/your_transcript.txt
```

---

## Mock mode

If `ANTHROPIC_API_KEY` is set to a placeholder value, the pipeline runs in **mock mode** — it derives a structured response from the transcript without calling the Claude API. All steps are clearly labeled `[MOCK]` in the console output.

This lets you test the full pipeline (Slides, Drive, Sheets) without consuming API credits.

---

## Cost tracking

Every Claude API call logs the following to `outputs/cost_report.json`:

```json
{
  "step": "summarization",
  "model": "claude-sonnet-4-6",
  "input_tokens": 12000,
  "output_tokens": 800,
  "cost_usd": 0.048,
  "timestamp": "2026-04-10T10:00:00Z"
}
```

A summary is printed to the console after every run:

```
=== COST SUMMARY ===
Step: summarization
Input tokens:  12,000  → $0.036
Output tokens:    800  → $0.012
Total this run:        $0.048
====================
```

### Pricing reference (`claude-sonnet-4-6`)

| Token type | Price |
|---|---|
| Input | $3.00 / 1M tokens |
| Output | $15.00 / 1M tokens |

### Monthly cost estimate (20 meetings/month, 60 min each)

| Component | Unit cost | Monthly cost |
|---|---|---|
| Claude API (~12K input + 900 output tokens) | ~$0.05/meeting | ~$1.00 |
| Whisper transcription (60 min) | $0.36/meeting | $7.20 |
| Google APIs (Slides, Drive, Sheets) | Free (within quota) | $0.00 |
| **Total** | | **~$8.20/month** |

---

## Assumptions

| Assumption | Value |
|---|---|
| Meeting duration | 60 minutes |
| Transcript length | ~8,000 words / ~12,000 tokens |
| Claude calls per run | 1 (single prompt) |
| Output tokens per call | ~800–1,000 |
| Meetings per month | 20 |
| Video/audio ingestion | Mocked (out of scope) |

---

## Out of scope

- Real video/audio ingestion and processing
- Authentication / SSO / multi-user
- Production-grade retries and error handling
- Cloud deployment (GCP, AWS)
- Automated scheduling / triggers
- Slide styling / branding / templates
