"""
transcriber.py — Mock transcriber that simulates the OpenAI Whisper API.
In a real pipeline this would call the Whisper API and return a transcript string.
Prints a [MOCK] label to make the simulation explicit.
"""

import os


def transcribe(audio_path: str) -> str:
    """
    Mock transcription: read a .txt file and return its contents as the transcript.
    Simulates what Whisper would return after processing a real audio/video file.
    Prints [MOCK] to signal this is not a real API call.
    """
    print(f"[MOCK] Whisper transcription skipped — reading local file: {audio_path}")

    if not os.path.exists(audio_path):
        raise FileNotFoundError(
            f"[MOCK] Transcript file not found at path: {audio_path}"
        )

    try:
        with open(audio_path, "r", encoding="utf-8") as f:
            transcript = f.read()
    except OSError as e:
        raise OSError(f"[MOCK] Failed to read transcript file '{audio_path}': {e}") from e

    word_count = len(transcript.split())
    print(f"[MOCK] Transcript loaded — {word_count:,} words (~{word_count * 1.5:.0f} tokens estimated)")
    return transcript


def store_transcript(transcript: str, output_path: str) -> str:
    """
    Mock GCS storage: save transcript to local filesystem.
    In a real pipeline this would upload to Google Cloud Storage.
    Prints [MOCK] to signal this is not a real upload.
    """
    print(f"[MOCK] GCS upload skipped — saving transcript locally to: {output_path}")

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(transcript)
    except OSError as e:
        raise OSError(f"[MOCK] Failed to save transcript to '{output_path}': {e}") from e

    print(f"[MOCK] Transcript stored at: {output_path}")
    return output_path
