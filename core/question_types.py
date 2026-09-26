"""
Central registry of the interactive question/answer formats the app
supports. Deliberately excludes plain multiple-choice — every format here
requires more than "click one of four buttons" to answer.

User-facing labels/descriptions live in core.i18n (per-language); this
module only holds the language-agnostic bits: type codes, icons, and the
JSON schema hints embedded directly into the OpenRouter prompt.
"""

FILL_BLANK = "fill_blank"
MATCHING = "matching"
ORDERING = "ordering"
MULTI_SELECT = "multi_select"
NUMERIC = "numeric"
CODE_COMPLETE = "code_complete"
CATEGORIZE = "categorize"
HOTSPOT_TEXT = "hotspot_text"

ALL_TYPES = [
    FILL_BLANK, MATCHING, ORDERING, MULTI_SELECT, NUMERIC, CODE_COMPLETE, CATEGORIZE, HOTSPOT_TEXT,
]

ICONS = {
    FILL_BLANK: "✏️",
    MATCHING: "🔗",
    ORDERING: "🔢",
    MULTI_SELECT: "🧩",
    NUMERIC: "🎚️",
    CODE_COMPLETE: "💻",
    CATEGORIZE: "🗂️",
    HOTSPOT_TEXT: "🖱️",
}

SCHEMA_HINTS = {
    FILL_BLANK: (
        '{"type":"fill_blank","prompt":"<sentence with a blank shown as ___>",'
        '"accepted_answers":["<answer1>","<synonym2>"],"explanation":"<1 sentence>"}'
    ),
    MATCHING: (
        '{"type":"matching","prompt":"<instruction>",'
        '"pairs":[{"id":"a","left":"<term>","right":"<matching definition>"}, '
        '... 4 to 6 pairs, unique ids a,b,c...],"explanation":"<1 sentence>"}'
    ),
    ORDERING: (
        '{"type":"ordering","prompt":"<instruction>",'
        '"items":[{"id":"1","text":"<item>"}, ... 4 to 6 items in SHUFFLED order],'
        '"correct_order":["<id>", "<id>", .... the ids in the correct order],'
        '"explanation":"<1 sentence>"}'
    ),
    MULTI_SELECT: (
        '{"type":"multi_select","prompt":"<instruction, make clear multiple answers are correct>",'
        '"options":[{"id":"a","text":"<option>"}, ... 4 to 6 options],'
        '"correct_ids":["<id>", ... 2 or more of the option ids],"explanation":"<1 sentence>"}'
    ),
    NUMERIC: (
        '{"type":"numeric","prompt":"<question with a numeric answer>",'
        '"answer":<number>,"tolerance":<number, how much slack is acceptable>,'
        '"min":<number, slider lower bound>,"max":<number, slider upper bound>,'
        '"unit":"<unit string or empty>","explanation":"<1 sentence>"}'
    ),
    CODE_COMPLETE: (
        '{"type":"code_complete","prompt":"<instruction>","language":"<e.g. python>",'
        '"code_template":"<code with the missing part shown as ___, use \\n for newlines>",'
        '"accepted_answers":["<exact text that completes it>", "<alt phrasing>"],'
        '"explanation":"<1 sentence>"}'
    ),
    CATEGORIZE: (
        '{"type":"categorize","prompt":"<instruction>",'
        '"categories":[{"id":"c1","name":"<category name>"}, ... 2 to 4 categories],'
        '"items":[{"id":"i1","text":"<item>","category_id":"<id of its correct category>"}, '
        '... 5 to 10 items in SHUFFLED order, each belonging to exactly one category],'
        '"explanation":"<1 sentence>"}'
    ),
    HOTSPOT_TEXT: (
        '{"type":"hotspot_text","prompt":"<instruction, e.g. Click every verb in this sentence>",'
        '"tokens":[{"id":"t1","text":"<single word or short chunk, in original reading order>"}, '
        '... split the passage into 6 to 20 clickable tokens],'
        '"correct_ids":["<id>", ... the token ids that answer the question, 1 or more],'
        '"explanation":"<1 sentence>"}'
    ),
}

REQUIRED_FIELDS = {
    FILL_BLANK: {"prompt", "accepted_answers"},
    MATCHING: {"prompt", "pairs"},
    ORDERING: {"prompt", "items", "correct_order"},
    MULTI_SELECT: {"prompt", "options", "correct_ids"},
    NUMERIC: {"prompt", "answer"},
    CODE_COMPLETE: {"prompt", "code_template", "accepted_answers"},
    CATEGORIZE: {"prompt", "categories", "items"},
    HOTSPOT_TEXT: {"prompt", "tokens", "correct_ids"},
}
