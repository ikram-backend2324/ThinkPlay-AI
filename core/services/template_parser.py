"""
Strict, deterministic (no AI call) parser for a documented fixed format:

    Q: What is the capital of France?
    A) London
    B) Paris
    C) Berlin
    D) Madrid
    Correct: B
    Explanation: Paris is the capital of France.

Also accepts "Q1:", "Q1)", "A.", and "Answer:" as equivalent spellings.
Produces multi_select-shaped questions (single correct option) so they still
render with the platform's styled chip grid rather than plain radio inputs.
"""

import re

from core.question_types import MULTI_SELECT

_QUESTION_PREFIX_RE = re.compile(r"^Q\d*[:.)]\s*", re.IGNORECASE)
_OPTION_RE = re.compile(r"^([A-Za-z])[).]\s*(.+)$")
_CORRECT_RE = re.compile(r"^(?:CORRECT|ANSWER)(?:\s+ANSWER)?\s*[:.]\s*(.+)$", re.IGNORECASE)
_EXPLANATION_RE = re.compile(r"^EXPLANATION\s*[:.]\s*(.+)$", re.IGNORECASE)


class TemplateParseError(Exception):
    pass


def parse_template(raw_text):
    lines = [line.strip() for line in raw_text.replace("\r\n", "\n").split("\n")]
    lines = [line for line in lines if line]

    questions = []
    current = None

    def flush():
        if current is None:
            return
        if not current["options"]:
            raise TemplateParseError(f'Question "{current["prompt"][:60]}" has no lettered options (A) ...).')
        if not current["correct"]:
            raise TemplateParseError(f'Question "{current["prompt"][:60]}" is missing a "Correct: <letter>" line.')
        options = [{"id": letter.lower(), "text": text} for letter, text in current["options"]]
        correct_letter = current["correct"].strip()[:1].lower()
        if not any(o["id"] == correct_letter for o in options):
            raise TemplateParseError(
                f'Question "{current["prompt"][:60]}": "Correct: {current["correct"]}" doesn\'t match any option letter.'
            )
        questions.append(
            {
                "type": MULTI_SELECT,
                "prompt": current["prompt"],
                "options": options,
                "correct_ids": [correct_letter],
                "explanation": current["explanation"],
            }
        )

    for line in lines:
        if _QUESTION_PREFIX_RE.match(line):
            flush()
            current = {
                "prompt": _QUESTION_PREFIX_RE.sub("", line).strip(),
                "options": [],
                "correct": None,
                "explanation": "",
            }
            continue
        if current is None:
            continue  # ignore stray text before the first question

        option_match = _OPTION_RE.match(line)
        if option_match:
            current["options"].append((option_match.group(1), option_match.group(2).strip()))
            continue

        correct_match = _CORRECT_RE.match(line)
        if correct_match:
            current["correct"] = correct_match.group(1).strip()
            continue

        explanation_match = _EXPLANATION_RE.match(line)
        if explanation_match:
            current["explanation"] = explanation_match.group(1).strip()
            continue
        # Any other line inside a question block is ignored rather than failing the upload.

    flush()

    if not questions:
        raise TemplateParseError(
            'No questions found. Each question must start with "Q:", followed by lettered '
            'options like "A) ...", and a "Correct: <letter>" line.'
        )
    return questions
