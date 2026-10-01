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
MAX_PARSE_TEXT_CHARS = 14000
MAX_PARSED_QUESTIONS = 80
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


def _build_prompt(subject_name, type_sequence, avoid_topics, language_name, difficulty=None, topic=None, source_text=None):
    focus = f"the subject: {subject_name}"
    if topic:
        focus = f"the topic \"{topic}\" (subject: {subject_name})"
    lines = [
        f"You are writing an interactive quiz on {focus}.",
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
    if source_text:
        lines.append(
            "\nBase every question strictly on the SOURCE MATERIAL below (the teacher's lecture). "
            "Do not ask about facts that are not in it, and keep the correct answers consistent with it."
            f"\n\nSOURCE MATERIAL:\n{source_text[:MAX_PARSE_TEXT_CHARS]}"
        )

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
    return _request_json(model, prompt).get("questions", [])


def _request_json(model, prompt, temperature=0.8):
    """Sends one chat request (with retries) and returns the JSON object the model replied with."""
    if not settings.OPENROUTER_API_KEY:
        raise GenerationError("OPENROUTER_API_KEY is not configured.")

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "X-Title": "TeachX",
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
        "temperature": temperature,
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
            if not isinstance(parsed, dict):
                raise ValueError("Expected a JSON object.")
            return parsed
        except (requests.RequestException, KeyError, ValueError, json.JSONDecodeError) as exc:
            last_error = exc
    raise GenerationError(f"Failed to reach OpenRouter after {MAX_ATTEMPTS} attempts: {last_error}")


def generate_question_batch(
    subject_name, interaction_types, count, avoid_topics=None, language=DEFAULT_LANGUAGE, difficulty=None,
    topic=None, source_text=None,
):
    """
    Returns a list of validated question dicts (length <= count — malformed
    entries are dropped rather than failing the whole batch). Raises
    GenerationError if OpenRouter can't be reached at all or every attempt
    returns unusable JSON.
    """
    type_sequence = _type_sequence(interaction_types, count)
    language_name = AI_LANGUAGE_NAMES.get(language, AI_LANGUAGE_NAMES[DEFAULT_LANGUAGE])
    prompt = _build_prompt(
        subject_name, type_sequence, avoid_topics or [], language_name, difficulty, topic=topic, source_text=source_text
    )
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


def generate_questions(
    subject_name, interaction_types, count, language=DEFAULT_LANGUAGE, difficulty=None, topic=None, source_text=None,
    batch_size=8,
):
    """
    Generates `count` questions in batches (one huge request is slow and less
    reliable). Returns what it has if a later batch fails; raises
    GenerationError only when nothing at all could be generated.
    """
    questions = []
    # A few spare batches cover the occasional malformed question; past that,
    # stop with what we have instead of calling the model indefinitely.
    batches_left = -(-count // batch_size) + 2
    while len(questions) < count and batches_left > 0:
        batches_left -= 1
        try:
            batch = generate_question_batch(
                subject_name=subject_name,
                interaction_types=interaction_types,
                count=min(batch_size, count - len(questions)),
                avoid_topics=[q["prompt"] for q in questions],
                language=language,
                difficulty=difficulty,
                topic=topic,
                source_text=source_text,
            )
        except GenerationError:
            if questions:
                break
            raise
        questions.extend(batch)
    return questions[:count]


def design_lesson(setting, competences, language=DEFAULT_LANGUAGE):
    """
    Asks the model to design a competence-oriented lesson with the SCAFFOLD
    toolkit. `setting` is the teacher's answers to the setting cards (topic,
    subject, duration, ...); `competences` a list of competence titles in
    English. Returns the validated plan dict (see _validate_plan).
    """
    from core.scaffold import english_digest

    language_name = AI_LANGUAGE_NAMES.get(language, AI_LANGUAGE_NAMES[DEFAULT_LANGUAGE])
    setting_lines = "\n".join(f"- {key}: {value}" for key, value in setting.items() if value)
    competence_lines = "\n".join(f"- {c}" for c in competences)
    prompt = (
        "You are a methodological assistant for teachers. Design ONE competence-oriented lesson using the "
        "SCAFFOLD toolkit (JRC & ETF, 2024). Choose methods ONLY from the codes listed below.\n\n"
        f"{english_digest()}\n\n"
        f"LESSON SETTING (from the teacher):\n{setting_lines}\n\n"
        f"COMPETENCES TO DEVELOP:\n{competence_lines}\n\n"
        "Return ONLY a JSON object with exactly these keys:\n"
        '{"learning_outcomes": ["<3-5 observable outcomes>"],\n'
        ' "teaching_method": {"code": "<one teaching method code>", "why": "<1-2 sentences>"},\n'
        ' "steps": ["<the chosen method steps adapted concretely to this lesson, 4-6 items>"],\n'
        ' "diagnostic_assessment": {"code": "<assessment code>", "how": "<how to check the starting level>"},\n'
        ' "output": "<what learners produce as evidence>",\n'
        ' "final_assessment": [{"code": "<assessment code>", "how": "<how>"}],\n'
        ' "resources": ["<resource>"],\n'
        ' "timeline": [{"minutes": <int>, "activity": "<what happens>"}],\n'
        ' "principles": ["<1-3 principle codes that this plan applies>"],\n'
        ' "quiz_topic": "<a short topic for an end-of-lesson quiz>"}\n'
        "The timeline minutes must add up to roughly the lesson duration. "
        f"Write every human-readable value in {language_name}; keep JSON keys and codes in English."
    )
    model = settings.OPENROUTER_MODEL_OVERRIDES.get(language) or settings.OPENROUTER_MODEL
    plan = validate_plan(_request_json(model, prompt, temperature=0.6))
    if plan is None:
        raise GenerationError("The AI returned a lesson plan in an unexpected format.")
    return plan


def validate_plan(raw):
    """Keeps only well-formed fields and codes that exist in the toolkit; None if the core is missing."""
    from core.scaffold import ASSESSMENTS_BY_CODE, METHODS_BY_CODE, PRINCIPLES_BY_CODE

    method = raw.get("teaching_method") if isinstance(raw, dict) else None
    if not isinstance(method, dict) or method.get("code") not in METHODS_BY_CODE:
        return None

    def strings(value, limit=12):
        return [str(v).strip() for v in value if str(v).strip()][:limit] if isinstance(value, list) else []

    def assessment(entry):
        if isinstance(entry, dict) and entry.get("code") in ASSESSMENTS_BY_CODE:
            return {"code": entry["code"], "how": str(entry.get("how", "")).strip()}
        return None

    timeline = []
    for row in raw.get("timeline") or []:
        if isinstance(row, dict) and str(row.get("activity", "")).strip():
            try:
                minutes = max(0, int(row.get("minutes") or 0))
            except (TypeError, ValueError):
                minutes = 0
            timeline.append({"minutes": minutes, "activity": str(row["activity"]).strip()})

    final = raw.get("final_assessment")
    if isinstance(final, dict):
        final = [final]
    return {
        "learning_outcomes": strings(raw.get("learning_outcomes")),
        "teaching_method": {"code": method["code"], "why": str(method.get("why", "")).strip()},
        "steps": strings(raw.get("steps")),
        "diagnostic_assessment": assessment(raw.get("diagnostic_assessment")),
        "output": str(raw.get("output", "")).strip(),
        "final_assessment": [a for a in (assessment(e) for e in (final or [])) if a],
        "resources": strings(raw.get("resources")),
        "timeline": timeline[:20],
        "principles": [p for p in strings(raw.get("principles")) if p in PRINCIPLES_BY_CODE][:3],
        "quiz_topic": str(raw.get("quiz_topic", "")).strip()[:200],
    }
