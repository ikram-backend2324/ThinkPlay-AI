"""
Server-side grading for each interactive question type. Never trust a
client-reported "correct" flag — always recompute from the question's
stored `data` and the submitted answer.
"""

from core.question_types import (
    CODE_COMPLETE, FILL_BLANK, MATCHING, MULTI_SELECT, NUMERIC, ORDERING,
)


def _normalize(text):
    return " ".join(str(text).strip().lower().split())


def _grade_fill_blank(data, submitted):
    accepted = {_normalize(a) for a in data.get("accepted_answers", [])}
    return _normalize(submitted.get("value", "")) in accepted


def _grade_matching(data, submitted):
    pairs = data.get("pairs", [])
    submitted_map = submitted.get("pairs", {})
    if not isinstance(submitted_map, dict) or len(submitted_map) != len(pairs):
        return False
    return all(submitted_map.get(pair["id"]) == pair["id"] for pair in pairs)


def _grade_ordering(data, submitted):
    correct_order = data.get("correct_order", [])
    submitted_order = submitted.get("order", [])
    return list(submitted_order) == list(correct_order)


def _grade_multi_select(data, submitted):
    correct_ids = set(data.get("correct_ids", []))
    submitted_ids = set(submitted.get("selected_ids", []))
    return submitted_ids == correct_ids


def _grade_numeric(data, submitted):
    try:
        value = float(submitted.get("value"))
    except (TypeError, ValueError):
        return False
    answer = float(data.get("answer", 0))
    tolerance = float(data.get("tolerance", 0) or 0)
    return abs(value - answer) <= tolerance


def _grade_code_complete(data, submitted):
    accepted = {_normalize(a) for a in data.get("accepted_answers", [])}
    return _normalize(submitted.get("value", "")) in accepted


GRADERS = {
    FILL_BLANK: _grade_fill_blank,
    MATCHING: _grade_matching,
    ORDERING: _grade_ordering,
    MULTI_SELECT: _grade_multi_select,
    NUMERIC: _grade_numeric,
    CODE_COMPLETE: _grade_code_complete,
}


def grade_answer(question_type, question_data, submitted_answer):
    grader = GRADERS.get(question_type)
    if grader is None or not isinstance(submitted_answer, dict):
        return False
    try:
        return bool(grader(question_data, submitted_answer))
    except Exception:
        return False
