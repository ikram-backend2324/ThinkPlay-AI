"""
Central registry of the interactive question/answer formats the app
supports. Deliberately excludes plain multiple-choice — every format here
requires more than "click one of four buttons" to answer.

Each entry's `schema_hint` is embedded directly into the OpenRouter prompt so
the model knows exactly which JSON shape to produce for that type.
"""

FILL_BLANK = "fill_blank"
MATCHING = "matching"
ORDERING = "ordering"
MULTI_SELECT = "multi_select"
NUMERIC = "numeric"
CODE_COMPLETE = "code_complete"

ALL_TYPES = [FILL_BLANK, MATCHING, ORDERING, MULTI_SELECT, NUMERIC, CODE_COMPLETE]

LABELS = {
    FILL_BLANK: "Fill in the Blank",
    MATCHING: "Drag & Drop Matching",
    ORDERING: "Sequence Ordering",
    MULTI_SELECT: "Select All That Apply",
    NUMERIC: "Numeric / Slider Answer",
    CODE_COMPLETE: "Code Completion",
}

DESCRIPTIONS = {
    FILL_BLANK: "Type the missing word or phrase into a sentence.",
    MATCHING: "Drag each term onto its matching definition.",
    ORDERING: "Drag items into the correct order or sequence.",
    MULTI_SELECT: "Tap every option that is correct — there may be several.",
    NUMERIC: "Drag a slider or type an exact number to answer.",
    CODE_COMPLETE: "Complete the missing piece of code.",
}

ICONS = {
    FILL_BLANK: "✏️",
    MATCHING: "🔗",
    ORDERING: "🔢",
    MULTI_SELECT: "🧩",
    NUMERIC: "🎚️",
    CODE_COMPLETE: "💻",
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
}

REQUIRED_FIELDS = {
    FILL_BLANK: {"prompt", "accepted_answers"},
    MATCHING: {"prompt", "pairs"},
    ORDERING: {"prompt", "items", "correct_order"},
    MULTI_SELECT: {"prompt", "options", "correct_ids"},
    NUMERIC: {"prompt", "answer"},
    CODE_COMPLETE: {"prompt", "code_template", "accepted_answers"},
}
