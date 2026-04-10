"""
ai_processor.py — Calls the Claude API (claude-sonnet-4-6) to process a meeting transcript
and returns structured JSON with executive summary, objectives, action items, and next steps.
Measures and logs token usage and cost on every call.
If ANTHROPIC_API_KEY is a placeholder, falls back to a mock response derived from the transcript.
"""

import json
import os
import re

import anthropic
from dotenv import load_dotenv

from cost_tracker import log_api_call

load_dotenv()

MODEL = "claude-sonnet-4-6"
_PLACEHOLDER_KEYS = {"your_key_here", "", "your-api-key", "sk-ant-placeholder"}

SYSTEM_PROMPT = """You are an expert meeting facilitator and business analyst.
Your task is to analyze a meeting transcript and extract key information in a structured JSON format.
Always respond with valid JSON only — no markdown, no explanation, just the raw JSON object."""

USER_PROMPT_TEMPLATE = """Analyze the following meeting transcript and return a JSON object with this exact structure:

{{
  "executive_summary": "A concise 2-3 sentence summary of the entire meeting",
  "objectives": [
    "High-level objective 1",
    "High-level objective 2",
    "High-level objective 3"
  ],
  "action_items": [
    "Specific actionable item 1 (owner: Name)",
    "Specific actionable item 2 (owner: Name)",
    "Specific actionable item 3 (owner: Name)"
  ],
  "next_steps": "Brief paragraph describing what happens after this meeting"
}}

TRANSCRIPT:
{transcript}"""


def _is_placeholder(api_key: str) -> bool:
    """Return True if the API key is a known placeholder value and should not be used."""
    return not api_key or api_key.strip() in _PLACEHOLDER_KEYS


def _build_mock_response(transcript: str) -> dict:
    """
    Build a mock structured response derived from the transcript text.
    Used when ANTHROPIC_API_KEY is a placeholder. Prints a [MOCK] label.
    """
    print("[MOCK] ANTHROPIC_API_KEY is a placeholder — using mock AI response.")

    # Extract speaker lines to infer participants and topics
    lines = [l.strip() for l in transcript.splitlines() if l.strip()]
    speakers = list(dict.fromkeys(
        m.group(1) for l in lines if (m := re.match(r"^([A-Z][a-z]+(?: [A-Z][a-z]+)+):", l))
    ))
    speaker_list = ", ".join(speakers[:4]) + ("..." if len(speakers) > 4 else "")

    # Derive a rough title from the first non-empty line
    title_line = next((l for l in lines if not re.match(r"^(Date|Attendees|---)", l)), "the meeting")

    # Collect lines that are short, imperative objectives (not full dialogue sentences)
    objective_pattern = r"^(Objective|Goal|Priority|Target)[\s\w]*:"
    objective_candidates = [
        l.split(":", 1)[-1].strip()
        for l in lines if re.match(objective_pattern, l, re.I) and len(l.split(":", 1)[-1].strip()) > 10
    ][:3]
    objectives = (
        objective_candidates
        if len(objective_candidates) == 3
        else [
            "Deliver the reporting MVP to unblock enterprise sales pipeline",
            "Improve mobile app performance to reach a 4.0+ App Store rating",
            "Ship AI-assisted search feature by end of Q2",
        ]
    )

    # Collect explicit first-person commitment lines with a deadline cue
    action_pattern = r"(I'll|I will)\b.{10,}.*(by |today|wednesday|tuesday|friday|april|may|end of)"
    action_candidates = [
        l for l in lines if re.search(action_pattern, l, re.I)
    ][:3]
    action_items = (
        action_candidates
        if len(action_candidates) == 3
        else [
            "Prepare detailed scope document for reporting MVP by Wednesday (owner: Marcus Williams)",
            "Deliver high-fidelity UX wireframes for reporting module by April 17th (owner: Laura Nguyen)",
            "Send competitive analysis of reporting features to the team by Tuesday (owner: Diana Flores)",
        ]
    )

    mock_tokens_in = len(transcript.split()) * 2      # rough estimate: ~2 tokens/word
    mock_tokens_out = 180

    log_api_call(
        step="summarization (mock)",
        model=f"{MODEL} [MOCK]",
        input_tokens=mock_tokens_in,
        output_tokens=mock_tokens_out,
    )

    return {
        "executive_summary": (
            f"The team held {title_line.lower()} with participation from {speaker_list}. "
            "Key priorities for Q2 were aligned, covering product delivery, performance, "
            "and AI capabilities. Owners and deadlines were assigned for all action items."
        ),
        "objectives": objectives,
        "action_items": action_items,
        "next_steps": (
            "The team will execute on the agreed deliverables over the next two weeks. "
            "A mid-sprint check-in is scheduled to review progress. Stakeholders will be "
            "updated on the reporting MVP timeline to accelerate pending enterprise deals."
        ),
    }


def process_transcript(transcript: str) -> dict:
    """
    Send the transcript to Claude and return parsed structured JSON.
    Falls back to a mock response if ANTHROPIC_API_KEY is a placeholder.
    Logs token usage and cost via cost_tracker after the call.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if _is_placeholder(api_key):
        result = _build_mock_response(transcript)
        _validate_structure(result)
        return result

    client = anthropic.Anthropic(api_key=api_key)

    prompt = USER_PROMPT_TEMPLATE.format(transcript=transcript)

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.AuthenticationError as e:
        raise PermissionError(f"Claude API authentication failed: {e}") from e
    except anthropic.RateLimitError as e:
        raise RuntimeError(f"Claude API rate limit exceeded: {e}") from e
    except anthropic.APIError as e:
        raise RuntimeError(f"Claude API error during transcript processing: {e}") from e

    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens

    log_api_call(
        step="summarization",
        model=MODEL,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )

    raw_text = response.content[0].text.strip()

    try:
        structured = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Claude returned invalid JSON. Raw response:\n{raw_text}\nError: {e}"
        ) from e

    _validate_structure(structured)
    return structured


def _validate_structure(data: dict) -> None:
    """Validate that the Claude response contains all required fields."""
    required_keys = ["executive_summary", "objectives", "action_items", "next_steps"]
    missing = [k for k in required_keys if k not in data]
    if missing:
        raise ValueError(
            f"Claude response missing required fields: {missing}. Got: {list(data.keys())}"
        )

    if not isinstance(data["objectives"], list) or len(data["objectives"]) < 1:
        raise ValueError("'objectives' must be a non-empty list.")

    if not isinstance(data["action_items"], list) or len(data["action_items"]) < 1:
        raise ValueError("'action_items' must be a non-empty list.")
