"""
Thin wrapper around OpenRouter's chat-completions endpoint, specialised for
generating one batch of structured quiz questions at a time.
"""

import itertools
import json

import requests
from django.conf import settings

from core.question_types import REQUIRED_FIELDS, SCHEMA_HINTS

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MAX_ATTEMPTS = 3
REQUEST_TIMEOUT = 60


class GenerationError(Exception):
    """Raised when OpenRouter can't be reached or never returns usable JSON."""


def _type_sequence(interaction_types, count):
    """Round-robin the chosen interaction types to fill exactly `count` slots."""
    cycle = itertools.cycle(interaction_types)
    return [next(cycle) for _ in range(count)]


def _build_prompt(subject_name, type_sequence, avoid_topics):
    lines = [
        f"You are writing an interactive quiz on the subject: {subject_name}.",
        f"Generate exactly {len(type_sequence)} questions, in this exact order of formats:",
    ]
    for i, qtype in enumerate(type_sequence, start=1):
        lines.append(f"{i}. type=\"{qtype}\" — shape: {SCHEMA_HINTS[qtype]}")

    lines.append(
        "\nReturn ONLY a JSON object of the form "
        '{"questions": [ <question 1>, <question 2>, ... ]} '
        "with no markdown fences and no commentary. "
        "Each question object must match the exact shape given for its type above, "
        "including the \"type\" field. Vary the difficulty and keep every question "
        "factually correct and unambiguous."
    )
    if avoid_topics:
        joined = "; ".join(avoid_topics[-20:])
        lines.append(f"\nDo not repeat these already-used question topics/prompts: {joined}")

    return "\n".join(lines)


def _validate_question(raw, expected_type):
    if not isinstance(raw, dict):
        return None
    if raw.get("type") != expected_type:
        return None
    required = REQUIRED_FIELDS.get(expected_type, set())
    if not required.issubset(raw.keys()):
        return None
    if not str(raw.get("prompt", "")).strip():
        return None
    return raw


def generate_question_batch(subject_name, interaction_types, count, avoid_topics=None):
    """
    Returns a list of validated question dicts (length <= count — malformed
    entries are dropped rather than failing the whole batch). Raises
    GenerationError if OpenRouter can't be reached at all or every attempt
    returns unusable JSON.
    """
    if not settings.OPENROUTER_API_KEY:
        raise GenerationError("OPENROUTER_API_KEY is not configured.")

    type_sequence = _type_sequence(interaction_types, count)
    prompt = _build_prompt(subject_name, type_sequence, avoid_topics or [])

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "X-Title": "Smart Test Platform",
    }
    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You output strict, valid JSON only. Never wrap it in markdown code fences.",
            },
            {"role": "user", "content": prompt},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.8,
    }

    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.post(
                OPENROUTER_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            raw_questions = parsed.get("questions", [])
        except (requests.RequestException, KeyError, ValueError, json.JSONDecodeError) as exc:
            last_error = exc
            continue

        validated = []
        for raw, expected in zip(raw_questions, type_sequence):
            cleaned = _validate_question(raw, expected)
            if cleaned is not None:
                validated.append(cleaned)
        if validated:
            return validated
        last_error = ValueError("OpenRouter response contained no valid questions.")

    raise GenerationError(f"Failed to generate questions after {MAX_ATTEMPTS} attempts: {last_error}")
