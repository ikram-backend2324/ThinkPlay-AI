"""
Turns a Question + its Answer into plain-text "your answer" / "correct
answer" strings for the read-only review page.
"""

from core.question_types import (
    CATEGORIZE, CODE_COMPLETE, FILL_BLANK, HOTSPOT_TEXT, MATCHING, MULTI_SELECT, NUMERIC, ORDERING,
)


def _fill_blank(data, submitted, t):
    your = submitted.get("value", "") or t["quiz_no_answer"]
    correct = " / ".join(data.get("accepted_answers", []))
    return your, correct


def _matching(data, submitted, t):
    pairs = {p["id"]: p for p in data.get("pairs", [])}
    submitted_map = submitted.get("pairs", {})
    your_lines = []
    correct_lines = []
    for pid, pair in pairs.items():
        target_id = submitted_map.get(pid)
        target_text = pairs.get(target_id, {}).get("right", t["quiz_unmatched"]) if target_id else t["quiz_unmatched"]
        your_lines.append(f"{pair['left']} → {target_text}")
        correct_lines.append(f"{pair['left']} → {pair['right']}")
    return "; ".join(your_lines), "; ".join(correct_lines)


def _ordering(data, submitted, t):
    items = {i["id"]: i["text"] for i in data.get("items", [])}
    your = " → ".join(items.get(i, "?") for i in submitted.get("order", []))
    correct = " → ".join(items.get(i, "?") for i in data.get("correct_order", []))
    return your or t["quiz_no_answer"], correct


def _multi_select(data, submitted, t):
    options = {o["id"]: o["text"] for o in data.get("options", [])}
    your = ", ".join(options.get(i, "?") for i in submitted.get("selected_ids", []))
    correct = ", ".join(options.get(i, "?") for i in data.get("correct_ids", []))
    return your or t["quiz_no_answer"], correct


def _numeric(data, submitted, t):
    unit = f" {data['unit']}" if data.get("unit") else ""
    your = submitted.get("value")
    your = f"{your}{unit}" if your is not None else t["quiz_no_answer"]
    correct = f"{data.get('answer')}{unit}"
    return your, correct


def _code_complete(data, submitted, t):
    your = submitted.get("value", "") or t["quiz_no_answer"]
    correct = " / ".join(data.get("accepted_answers", []))
    return your, correct


def _categorize(data, submitted, t):
    categories = {c["id"]: c["name"] for c in data.get("categories", [])}
    submitted_map = submitted.get("assignments", {})
    your_lines = []
    correct_lines = []
    for item in data.get("items", []):
        your_cat = categories.get(submitted_map.get(item["id"]), t["quiz_unmatched"])
        correct_cat = categories.get(item["category_id"], "?")
        your_lines.append(f"{item['text']} → {your_cat}")
        correct_lines.append(f"{item['text']} → {correct_cat}")
    return "; ".join(your_lines), "; ".join(correct_lines)


def _hotspot_text(data, submitted, t):
    tokens = {tok["id"]: tok["text"] for tok in data.get("tokens", [])}
    your = ", ".join(tokens.get(i, "?") for i in submitted.get("selected_ids", []))
    correct = ", ".join(tokens.get(i, "?") for i in data.get("correct_ids", []))
    return your or t["quiz_no_answer"], correct


DESCRIBERS = {
    FILL_BLANK: _fill_blank,
    MATCHING: _matching,
    ORDERING: _ordering,
    MULTI_SELECT: _multi_select,
    NUMERIC: _numeric,
    CODE_COMPLETE: _code_complete,
    CATEGORIZE: _categorize,
    HOTSPOT_TEXT: _hotspot_text,
}


def describe_answer(question_type, question_data, submitted_data, t):
    describer = DESCRIBERS.get(question_type)
    if not describer:
        return "(unsupported)", "(unsupported)"
    return describer(question_data, submitted_data or {}, t)
