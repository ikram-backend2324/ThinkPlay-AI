"""
What the browser is allowed to see of a question.

The quiz page needs a question's text and options to render it, but never the
answer key: grading happens on the server (core.grading), and anything sent
to the page can be read in its source. `client_data` strips every answer
field; matching questions additionally get opaque ids for their right-hand
side, which `server_answer` maps back when the answers come in.
"""

import hashlib
import hmac

from django.conf import settings

from core.question_types import (
    CATEGORIZE, CODE_COMPLETE, FILL_BLANK, HOTSPOT_TEXT, MATCHING, MULTI_SELECT, NUMERIC, ORDERING,
)

# Fields that reveal the answer, per type (plus "explanation" for all of them).
_SECRET_FIELDS = {
    FILL_BLANK: {"accepted_answers"},
    CODE_COMPLETE: {"accepted_answers"},
    MULTI_SELECT: {"correct_ids"},
    HOTSPOT_TEXT: {"correct_ids"},
    ORDERING: {"correct_order"},
    NUMERIC: {"answer", "tolerance"},
    CATEGORIZE: set(),  # handled below: the secret is inside each item
    MATCHING: set(),  # handled below: pairs are split into two columns
}


def _token(question_id, pair_id):
    message = f"{question_id}:{pair_id}".encode()
    return hmac.new(settings.SECRET_KEY.encode(), message, hashlib.sha256).hexdigest()[:12]


def _numeric_bounds(data):
    """The slider range, worked out here because it can depend on the (secret) answer."""
    try:
        answer = float(data.get("answer") or 0)
        tolerance = float(data.get("tolerance") or 0) or max(1.0, abs(answer) * 0.1)
    except (TypeError, ValueError):
        answer, tolerance = 0.0, 1.0
    low = data.get("min")
    high = data.get("max")
    low = float(low) if isinstance(low, (int, float)) else answer - tolerance * 8 - 5
    high = float(high) if isinstance(high, (int, float)) else answer + tolerance * 8 + 5
    return low, high


def client_data(question_id, qtype, data):
    """A copy of the question data that is safe to put into the page."""
    safe = {k: v for k, v in data.items() if k not in _SECRET_FIELDS.get(qtype, set()) and k != "explanation"}

    if qtype == NUMERIC:
        safe["min"], safe["max"] = _numeric_bounds(data)
    elif qtype == CATEGORIZE:
        safe["items"] = [{"id": i.get("id"), "text": i.get("text", "")} for i in data.get("items", [])]
    elif qtype == MATCHING:
        pairs = data.get("pairs", [])
        safe.pop("pairs", None)
        safe["lefts"] = [{"id": p.get("id"), "text": p.get("left", "")} for p in pairs]
        safe["rights"] = [{"id": _token(question_id, p.get("id")), "text": p.get("right", "")} for p in pairs]
    return safe


def server_answer(question_id, qtype, data, submitted):
    """Turns a submitted answer back into the shape core.grading expects."""
    if qtype != MATCHING or not isinstance(submitted.get("pairs"), dict):
        return submitted
    by_token = {_token(question_id, p.get("id")): p.get("id") for p in data.get("pairs", [])}
    pairs = {left: by_token[token] for left, token in submitted["pairs"].items() if token in by_token}
    return {**submitted, "pairs": pairs}
