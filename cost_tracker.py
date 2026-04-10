"""
cost_tracker.py — Registers the cost of each API call and writes to outputs/cost_report.json.
"""

import json
import os
from datetime import datetime, timezone


COST_REPORT_PATH = os.path.join("outputs", "cost_report.json")

# Pricing for claude-sonnet-4-6
INPUT_PRICE_PER_MILLION = 3.00
OUTPUT_PRICE_PER_MILLION = 15.00


def calculate_cost(input_tokens: int, output_tokens: int) -> float:
    """Calculate total cost in USD for a Claude API call based on token counts."""
    return (input_tokens / 1_000_000 * INPUT_PRICE_PER_MILLION) + \
           (output_tokens / 1_000_000 * OUTPUT_PRICE_PER_MILLION)


def build_entry(step: str, model: str, input_tokens: int, output_tokens: int) -> dict:
    """Build a cost report entry dict for a single API call."""
    cost_usd = calculate_cost(input_tokens, output_tokens)
    return {
        "step": step,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": round(cost_usd, 6),
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def save_entry(entry: dict) -> None:
    """Append a cost entry to outputs/cost_report.json, creating the file if needed."""
    os.makedirs("outputs", exist_ok=True)

    existing: list = []
    if os.path.exists(COST_REPORT_PATH):
        try:
            with open(COST_REPORT_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                existing = data if isinstance(data, list) else [data]
        except (json.JSONDecodeError, OSError):
            existing = []

    existing.append(entry)

    with open(COST_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)


def print_cost_summary(entry: dict) -> None:
    """Print a human-readable cost summary to the console for a single API call entry."""
    input_cost = entry["input_tokens"] / 1_000_000 * INPUT_PRICE_PER_MILLION
    output_cost = entry["output_tokens"] / 1_000_000 * OUTPUT_PRICE_PER_MILLION

    print("\n=== COST SUMMARY ===")
    print(f"Step: {entry['step']}")
    print(f"Input tokens:  {entry['input_tokens']:>7,}  -> ${input_cost:.3f}")
    print(f"Output tokens: {entry['output_tokens']:>7,}  -> ${output_cost:.3f}")
    print(f"Total this run:        ${entry['cost_usd']:.3f}")
    print("====================\n")


def log_api_call(step: str, model: str, input_tokens: int, output_tokens: int) -> dict:
    """
    Full pipeline: calculate cost, save entry to JSON, and print summary.
    Returns the entry dict for downstream use.
    """
    entry = build_entry(step, model, input_tokens, output_tokens)
    save_entry(entry)
    print_cost_summary(entry)
    return entry
