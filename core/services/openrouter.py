"""
Thin wrapper around OpenRouter's chat-completions endpoint, specialised for
generating one batch of structured quiz questions at a time.
"""

import itertools
import json

import requests
from django.conf import settings

from core.i18n import AI_LANGUAGE_NAMES, DEFAULT_LANGUAGE
from core.question_types import REQUIRED_FIELDS, SCHEMA_HINTS

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MAX_ATTEMPTS = 3
REQUEST_TIMEOUT = 60

DIFFICULTY_HINTS = {
    "easy": "Easy: fundamental recall and basic definitions, suitable for a beginner.",
    "normal": "Normal: standard coursework-level application of concepts.",
    "hard": "Hard: multi-step reasoning, combining more than one concept per question.",
    "expert": "Expert: advanced, nuanced edge cases that would challenge a strong student.",
}


class GenerationError(Exception):
    """Raised when OpenRouter can't be reached or never returns usable JSON."""


def _type_sequence(interaction_types, count):
    """Round-robin the chosen interaction types to fill exactly `count` slots."""
    cycle = itertools.cycle(interaction_types)
    return [next(cycle) for _ in range(count)]


def _build_prompt(subject_name, type_sequence, avoid_topics, language_name, difficulty=None):
    lines = [
        f"You are writing an interactive quiz on the subject: {subject_name}.",
        f"Generate exactly {len(type_sequence)} questions, in this exact order of formats:",
    ]
    for i, qtype in enumerate(type_sequence, start=1):
        lines.append(f"{i}. type=\"{qtype}\" — shape: {SCHEMA_HINTS[qtype]}")

    difficulty_line = DIFFICULTY_HINTS.get(difficulty)
    consistency = (
        "Vary the difficulty and keep every question factually correct and unambiguous."
        if not difficulty_line
        else f"Target this difficulty level consistently for every question: {difficulty_line} "
        "Keep every question factually correct and unambiguous."
    )
    lines.append(
        "\nReturn ONLY a JSON object of the form "
        '{"questions": [ <question 1>, <question 2>, ... ]} '
        "with no markdown fences and no commentary. "
        "Each question object must match the exact shape given for its type above, "
        f"including the \"type\" field. {consistency}"
    )
    lines.append(
        f"\nWrite every human-readable text value (prompt, explanation, left/right terms, "
        f"item text, option text, accepted_answers, unit) in {language_name} — the actual "
        f"{language_name} language specifically, with its own genuine vocabulary and "
        "grammar, not a different but related language and not a machine-transliterated "
        f"approximation. If you are not confident in {language_name}, still write your best "
        f"genuine {language_name}, but never silently substitute a different language. "
        "Keep all JSON field/key names and every \"type\" value exactly as specified "
        "in English — only translate the natural-language VALUES, never the keys. "
        "Exception: for code_complete questions, the \"language\" field must still name "
        "a programming language (e.g. \"python\"), and code_template/accepted_answers "
        "code snippets stay in that programming language — only the surrounding "
        f"prompt/explanation text should be written in {language_name}."
    )
    if avoid_topics:
        joined = "; ".join(avoid_topics[-20:])
        lines.append(f"\nDo not repeat these already-used question topics/prompts: {joined}")

    return "\n".join(lines)


def _validate_question(raw, expected_type=None, allowed_types=None):
    if not isinstance(raw, dict):
        return None
    qtype = raw.get("type")
    if expected_type is not None and qtype != expected_type:
        return None
    if allowed_types is not None and qtype not in allowed_types:
        return None
    required = REQUIRED_FIELDS.get(qtype, set())
    if not required.issubset(raw.keys()):
        return None
    if not str(raw.get("prompt", "")).strip():
        return None
    return raw


def _call_openrouter(model, prompt):
    """
    Makes the actual request (with retries) and returns the raw list under
    "questions" in the response — no per-question validation here, callers
    validate against whatever shape they expect.
    """
    if not settings.OPENROUTER_API_KEY:
        raise GenerationError("OPENROUTER_API_KEY is not configured.")

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "X-Title": "Smart Test Platform",
    }
    payload = {
        "model": model,
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
            return parsed.get("questions", [])
        except (requests.RequestException, KeyError, ValueError, json.JSONDecodeError) as exc:
            last_error = exc
    raise GenerationError(f"Failed to reach OpenRouter after {MAX_ATTEMPTS} attempts: {last_error}")


def generate_question_batch(
    subject_name, interaction_types, count, avoid_topics=None, language=DEFAULT_LANGUAGE, difficulty=None
):
    """
    Returns a list of validated question dicts (length <= count — malformed
    entries are dropped rather than failing the whole batch). Raises
    GenerationError if OpenRouter can't be reached at all or every attempt
    returns unusable JSON.
    """
    type_sequence = _type_sequence(interaction_types, count)
    language_name = AI_LANGUAGE_NAMES.get(language, AI_LANGUAGE_NAMES[DEFAULT_LANGUAGE])
    prompt = _build_prompt(subject_name, type_sequence, avoid_topics or [], language_name, difficulty)
    model = settings.OPENROUTER_MODEL_OVERRIDES.get(language) or settings.OPENROUTER_MODEL

    raw_questions = _call_openrouter(model, prompt)
    validated = []
    for raw, expected in zip(raw_questions, type_sequence):
        cleaned = _validate_question(raw, expected_type=expected)
        if cleaned is not None:
            validated.append(cleaned)
    if not validated:
        raise GenerationError("OpenRouter response contained no valid questions.")
    return validated


MAX_PARSE_TEXT_CHARS = 14000
MAX_PARSED_QUESTIONS = 80


def _build_parse_prompt(subject_name, raw_text, interaction_types, language_name):
    type_hints = "\n".join(f'- type="{t}" — shape: {SCHEMA_HINTS[t]}' for t in interaction_types)
    return (
        f"You are converting an existing exam/quiz document (subject: {subject_name}) into "
        "structured interactive quiz questions.\n\n"
        "Identify every distinct question in the SOURCE TEXT below (there may be anywhere "
        f"from 1 to {MAX_PARSED_QUESTIONS}) and convert EACH one into one JSON question "
        "object. Preserve the original questions and correct answers faithfully — do not "
        "invent new questions, do not change what's being asked or what the correct answer "
        "is, and do not skip any. If a question's original format doesn't map cleanly onto "
        "one of the allowed types below, pick the closest reasonable one and adapt the "
        "presentation without changing the substance.\n\n"
        f"Allowed formats to convert into (pick whichever fits each question, vary them "
        f"across the set where reasonable):\n{type_hints}\n\n"
        'Return ONLY a JSON object of the form {"questions": [ <question 1>, ... ]} with no '
        "markdown fences and no commentary. Each object must match the exact shape given "
        "for its type above, including the \"type\" field.\n\n"
        f"Write every human-readable text value in {language_name}, matching the language "
        "the source text is already written in if it differs — preserve the source "
        "language's content faithfully rather than translating it. Keep all JSON field/key "
        "names and \"type\" values exactly as specified in English. For code_complete "
        "questions, \"language\" still names a programming language and code stays code.\n\n"
        f"SOURCE TEXT:\n{raw_text[:MAX_PARSE_TEXT_CHARS]}"
    )


def parse_document_to_questions(raw_text, subject_name, interaction_types, language=DEFAULT_LANGUAGE):
    """
    Converts the extracted text of a teacher-uploaded document into our
    question schema via OpenRouter. Raises GenerationError if it can't be
    reached or never returns any usable question.
    """
    language_name = AI_LANGUAGE_NAMES.get(language, AI_LANGUAGE_NAMES[DEFAULT_LANGUAGE])
    prompt = _build_parse_prompt(subject_name, raw_text, interaction_types, language_name)
    model = settings.OPENROUTER_MODEL_OVERRIDES.get(language) or settings.OPENROUTER_MODEL

    raw_questions = _call_openrouter(model, prompt)
    validated = []
    for raw in raw_questions[:MAX_PARSED_QUESTIONS]:
        cleaned = _validate_question(raw, allowed_types=set(interaction_types))
        if cleaned is not None:
            validated.append(cleaned)
    if not validated:
        raise GenerationError("Couldn't extract any valid questions from that document.")
    return validated
