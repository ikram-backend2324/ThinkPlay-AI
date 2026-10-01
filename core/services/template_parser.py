"""
Strict, deterministic (no AI call) parser for a documented plain-text format.
Every question starts with "Q:" and may declare its interactive format with a
"Type:" line. Without "Type:" a question is a lettered-options question:

    Q: What is the capital of France?
    A) London
    B) Paris
    Correct: B
    Explanation: Paris is the capital of France.

The other formats:

    Q: The capital of Uzbekistan is ___.
    Type: fill_blank
    Answer: Tashkent | Toshkent

    Q: Match each country with its capital.
    Type: matching
    France = Paris
    Japan = Tokyo

    Q: Put the planets in order from the Sun.
    Type: ordering
    1) Mercury
    2) Venus
    3) Earth

    Q: How many degrees are in a right angle?
    Type: numeric
    Answer: 90
    Tolerance: 0        (optional, default 0)
    Unit: °             (optional)
    Min: 0  Max: 180    (optional slider bounds, one per line)

    Q: Sort the animals.
    Type: categorize
    Mammals: Dog; Whale
    Birds: Eagle; Penguin

    Q: Click every verb.
    Type: hotspot
    Text: The cat [sat] on the mat and [purred].

    Q: Complete the loop.
    Type: code
    Language: python
    Code:
    for i in ___(5):
        print(i)
    Answer: range

Keywords are also accepted in Uzbek, Karakalpak and Russian (see KEYWORDS), so
teachers can write templates in their own language. Every format may carry an
"Explanation:" line.
"""

import random
import re

from core.question_types import (
    CATEGORIZE, CODE_COMPLETE, FILL_BLANK, HOTSPOT_TEXT, MATCHING, MULTI_SELECT, NUMERIC, ORDERING,
)


class TemplateParseError(Exception):
    pass


# Canonical keyword -> spellings accepted at the start of a line (case-insensitive).
KEYWORDS = {
    "question": ["q", "question", "savol", "soraw", "вопрос"],
    "type": ["type", "tur", "turi", "túri", "тип"],
    "correct": ["correct", "correct answer", "answer", "javob", "to'g'ri javob", "toʻgʻri javob", "juwap", "ответ", "правильный ответ"],
    "explanation": ["explanation", "izoh", "túsindirme", "tusindirme", "пояснение", "объяснение"],
    "tolerance": ["tolerance", "xatolik", "qátelik", "допуск", "погрешность"],
    "unit": ["unit", "birlik", "единица"],
    "min": ["min", "минимум"],
    "max": ["max", "максимум"],
    "text": ["text", "matn", "tekst", "текст"],
    "code": ["code", "kod", "код"],
    "language": ["language", "til", "язык"],
}

# Accepted "Type:" values -> question type code.
TYPE_ALIASES = {
    "choice": MULTI_SELECT, "multiple choice": MULTI_SELECT, "multi_select": MULTI_SELECT, "multi select": MULTI_SELECT,
    "test": MULTI_SELECT, "variant": MULTI_SELECT, "выбор": MULTI_SELECT,
    "fill_blank": FILL_BLANK, "fill blank": FILL_BLANK, "fill in the blank": FILL_BLANK, "blank": FILL_BLANK,
    "bo'sh joy": FILL_BLANK, "boʻsh joy": FILL_BLANK, "bos orın": FILL_BLANK, "пропуск": FILL_BLANK,
    "matching": MATCHING, "match": MATCHING, "moslashtirish": MATCHING, "sáykeslendiriw": MATCHING, "сопоставление": MATCHING,
    "ordering": ORDERING, "order": ORDERING, "sequence": ORDERING, "tartib": ORDERING, "izbe-izlik": ORDERING,
    "порядок": ORDERING, "последовательность": ORDERING,
    "numeric": NUMERIC, "number": NUMERIC, "slider": NUMERIC, "son": NUMERIC, "san": NUMERIC, "число": NUMERIC,
    "categorize": CATEGORIZE, "categories": CATEGORIZE, "guruhlash": CATEGORIZE, "toparlaw": CATEGORIZE,
    "категории": CATEGORIZE, "группировка": CATEGORIZE,
    "hotspot": HOTSPOT_TEXT, "hotspot_text": HOTSPOT_TEXT, "highlight": HOTSPOT_TEXT, "belgilash": HOTSPOT_TEXT,
    "belgilew": HOTSPOT_TEXT, "выделение": HOTSPOT_TEXT,
    "code": CODE_COMPLETE, "code_complete": CODE_COMPLETE, "kod": CODE_COMPLETE, "код": CODE_COMPLETE,
}

_APOSTROPHES = str.maketrans({"ʻ": "'", "ʼ": "'", "‘": "'", "’": "'", "`": "'"})


def _keyword_line(line):
    """Returns (keyword, value) if the line starts with a known "Keyword:" prefix, else (None, None)."""
    head, sep, rest = line.partition(":")
    if not sep:
        return None, None
    # "Q1:" / "Savol 3:" — allow a trailing question number on the question keyword.
    key = re.sub(r"\s*\d+$", "", head.strip().lower().translate(_APOSTROPHES))
    for canonical, spellings in KEYWORDS.items():
        if key in spellings:
            return canonical, rest.strip()
    return None, None


_QUESTION_ALT_RE = re.compile(r"^(?:q|savol|soraw|вопрос)\s*\d+\s*[.)]\s*(.+)$", re.IGNORECASE)
_OPTION_RE = re.compile(r"^([A-Za-zА-Яа-я])[).]\s*(.+)$")
_NUMBERED_RE = re.compile(r"^\d+\s*[).]\s*(.+)$")
_BULLET_RE = re.compile(r"^[-•*–]\s*(.+)$")
_PAIR_RE = re.compile(r"^(.+?)\s*(?:=|->|→|—>|=>)\s*(.+)$")


def _split_answers(value):
    return [a.strip() for a in re.split(r"\s*[|;]\s*", value) if a.strip()]


def _parse_number(value, label, prompt):
    try:
        return float(value.replace(",", ".").strip())
    except ValueError:
        raise TemplateParseError(f'Question "{prompt[:60]}": "{label}" must be a number, got "{value}".')


def _fail(prompt, message):
    raise TemplateParseError(f'Question "{prompt[:60]}": {message}')


def _build_choice(block):
    prompt = block["prompt"]
    options, correct = [], None
    for line in block["body"]:
        m = _OPTION_RE.match(line)
        if m:
            options.append({"id": m.group(1).lower(), "text": m.group(2).strip()})
    correct = block["fields"].get("correct")
    if not options:
        _fail(prompt, "has no lettered options (A) ...).")
    if not correct:
        _fail(prompt, 'is missing a "Correct: <letter>" line.')
    letters = [c.lower() for c in re.findall(r"[A-Za-zА-Яа-я]", correct)]
    option_ids = {o["id"] for o in options}
    if not letters or any(letter not in option_ids for letter in letters):
        _fail(prompt, f'"Correct: {correct}" doesn\'t match the option letters.')
    return {"type": MULTI_SELECT, "prompt": prompt, "options": options, "correct_ids": sorted(set(letters))}


def _build_fill_blank(block):
    prompt = block["prompt"]
    answers = _split_answers(block["fields"].get("correct", ""))
    if "___" not in prompt:
        _fail(prompt, 'must contain "___" where the blank goes.')
    if not answers:
        _fail(prompt, 'is missing an "Answer:" line.')
    return {"type": FILL_BLANK, "prompt": prompt, "accepted_answers": answers}


def _build_matching(block):
    prompt = block["prompt"]
    pairs = []
    for line in block["body"]:
        m = _PAIR_RE.match(_strip_list_marker(line))
        if m:
            pairs.append({"id": chr(ord("a") + len(pairs)), "left": m.group(1).strip(), "right": m.group(2).strip()})
    if len(pairs) < 2:
        _fail(prompt, 'needs at least 2 "term = definition" lines.')
    if len(pairs) > 26:
        _fail(prompt, "has too many pairs (max 26).")
    return {"type": MATCHING, "prompt": prompt, "pairs": pairs}


def _build_ordering(block):
    prompt = block["prompt"]
    steps = [_strip_list_marker(line) for line in block["body"] if _is_list_line(line)]
    if len(steps) < 2:
        _fail(prompt, 'needs at least 2 numbered steps ("1) ...") in the correct order.')
    items = [{"id": str(i + 1), "text": text} for i, text in enumerate(steps)]
    correct_order = [item["id"] for item in items]
    shuffled = items[:]
    # Shuffle so the correct order isn't simply the displayed one.
    while len(shuffled) > 1 and [i["id"] for i in shuffled] == correct_order:
        random.shuffle(shuffled)
    return {"type": ORDERING, "prompt": prompt, "items": shuffled, "correct_order": correct_order}


def _build_numeric(block):
    prompt = block["prompt"]
    fields = block["fields"]
    if not fields.get("correct"):
        _fail(prompt, 'is missing an "Answer: <number>" line.')
    answer = _parse_number(fields["correct"], "Answer", prompt)
    tolerance = abs(_parse_number(fields["tolerance"], "Tolerance", prompt)) if fields.get("tolerance") else 0
    span = max(abs(answer), 10)
    low = _parse_number(fields["min"], "Min", prompt) if fields.get("min") else answer - span
    high = _parse_number(fields["max"], "Max", prompt) if fields.get("max") else answer + span
    if not low <= answer <= high:
        _fail(prompt, "the answer must lie between Min and Max.")
    return {
        "type": NUMERIC, "prompt": prompt, "answer": answer, "tolerance": tolerance,
        "min": low, "max": high, "unit": fields.get("unit", ""),
    }


def _build_categorize(block):
    prompt = block["prompt"]
    categories, items = [], []
    for line in block["body"]:
        name, sep, rest = _strip_list_marker(line).partition(":")
        if not sep or not rest.strip():
            continue
        cid = f"c{len(categories) + 1}"
        categories.append({"id": cid, "name": name.strip()})
        for text in _split_answers(rest):
            items.append({"id": f"i{len(items) + 1}", "text": text, "category_id": cid})
    if len(categories) < 2:
        _fail(prompt, 'needs at least 2 "Category: item; item" lines.')
    random.shuffle(items)
    return {"type": CATEGORIZE, "prompt": prompt, "categories": categories, "items": items}


def _build_hotspot(block):
    prompt = block["prompt"]
    text = block["fields"].get("text") or " ".join(block["body"])
    if "[" not in text:
        _fail(prompt, 'needs a "Text:" line with the correct words in [square brackets].')
    tokens, correct_ids = [], []
    for chunk in re.findall(r"\[[^\]]+\]|[^\s\[\]]+", text):
        tid = f"t{len(tokens) + 1}"
        if chunk.startswith("["):
            tokens.append({"id": tid, "text": chunk[1:-1].strip()})
            correct_ids.append(tid)
        else:
            tokens.append({"id": tid, "text": chunk})
    return {"type": HOTSPOT_TEXT, "prompt": prompt, "tokens": tokens, "correct_ids": correct_ids}


def _build_code(block):
    prompt = block["prompt"]
    code = "\n".join(block["code_lines"]).strip("\n")
    answers = _split_answers(block["fields"].get("correct", ""))
    if "___" not in code:
        _fail(prompt, 'needs a "Code:" section containing "___" where the missing part goes.')
    if not answers:
        _fail(prompt, 'is missing an "Answer:" line.')
    return {
        "type": CODE_COMPLETE, "prompt": prompt, "language": block["fields"].get("language") or "code",
        "code_template": code, "accepted_answers": answers,
    }


BUILDERS = {
    MULTI_SELECT: _build_choice,
    FILL_BLANK: _build_fill_blank,
    MATCHING: _build_matching,
    ORDERING: _build_ordering,
    NUMERIC: _build_numeric,
    CATEGORIZE: _build_categorize,
    HOTSPOT_TEXT: _build_hotspot,
    CODE_COMPLETE: _build_code,
}


def _is_list_line(line):
    return bool(_NUMBERED_RE.match(line) or _BULLET_RE.match(line))


def _strip_list_marker(line):
    m = _NUMBERED_RE.match(line) or _BULLET_RE.match(line)
    return m.group(1).strip() if m else line.strip()


def _resolve_type(value, prompt):
    key = " ".join(value.lower().translate(_APOSTROPHES).replace("-", " ").split())
    qtype = TYPE_ALIASES.get(key) or TYPE_ALIASES.get(key.replace(" ", "_"))
    if not qtype:
        _fail(prompt, f'unknown "Type: {value}".')
    return qtype


def _new_block(prompt):
    return {"prompt": prompt, "type_value": None, "fields": {}, "body": [], "code_lines": [], "in_code": False}


def parse_template(raw_text):
    blocks = []
    current = None

    for raw_line in raw_text.replace("\r\n", "\n").split("\n"):
        line = raw_line.strip()
        keyword, value = _keyword_line(line) if line else (None, None)
        alt_question = _QUESTION_ALT_RE.match(line) if line and not keyword else None

        if keyword == "question" or alt_question:
            current = _new_block(value if keyword else alt_question.group(1).strip())
            blocks.append(current)
            continue
        if current is None:
            continue  # ignore stray text before the first question

        if current["in_code"]:
            # Inside a Code: section every line is kept verbatim (indentation matters)
            # until a recognised keyword line such as "Answer:" ends it.
            if keyword and keyword != "code":
                current["in_code"] = False
            else:
                current["code_lines"].append(raw_line.rstrip())
                continue

        if not line:
            continue
        if keyword == "type":
            current["type_value"] = value
        elif keyword == "code":
            current["in_code"] = True
            if value:
                current["code_lines"].append(value)
        elif keyword:
            current["fields"][keyword] = value
        else:
            current["body"].append(line)

    questions = []
    for block in blocks:
        if not block["prompt"]:
            raise TemplateParseError('Found a "Q:" line with no question text after it.')
        qtype = _resolve_type(block["type_value"], block["prompt"]) if block["type_value"] else MULTI_SELECT
        question = BUILDERS[qtype](block)
        question["explanation"] = block["fields"].get("explanation", "")
        questions.append(question)

    if not questions:
        raise TemplateParseError(
            'No questions found. Each question must start with "Q:" (see the template format on this page).'
        )
    return questions
