"""
Points, speed bonus, badges and the class leaderboard.

Points: every correct answer is worth BASE_POINTS plus a speed bonus of up to
MAX_SPEED_BONUS that shrinks linearly to zero at the question type's time
limit. Wrong answers earn nothing, so answering fast only pays off when the
answer is also right. The percentage score stays the official grade; points
are purely for motivation.
"""

from django.db.models import Count, Sum

from core.models import Badge, Profile, TestSession
from core.question_types import (
    CATEGORIZE, CODE_COMPLETE, FILL_BLANK, HOTSPOT_TEXT, MATCHING, MULTI_SELECT, NUMERIC, ORDERING,
)

BASE_POINTS = 100
MAX_SPEED_BONUS = 50
MIN_SECONDS = 2  # anything faster is treated as this, so a bogus 0 s can't max out the bonus

# Seconds after which a correct answer no longer earns a speed bonus.
TIME_LIMITS = {
    FILL_BLANK: 30,
    MULTI_SELECT: 30,
    NUMERIC: 30,
    HOTSPOT_TEXT: 40,
    ORDERING: 45,
    MATCHING: 60,
    CATEGORIZE: 60,
    CODE_COMPLETE: 60,
}
DEFAULT_TIME_LIMIT = 45


def clean_seconds(value):
    """Coerces a browser-reported duration into a sane float of seconds."""
    try:
        seconds = float(value)
    except (TypeError, ValueError):
        return 0.0
    if seconds != seconds or seconds < 0:  # NaN or negative
        return 0.0
    return min(seconds, 3600.0)


def speed_bonus(question_type, seconds):
    limit = TIME_LIMITS.get(question_type, DEFAULT_TIME_LIMIT)
    seconds = max(seconds, MIN_SECONDS)
    if seconds >= limit:
        return 0
    return round(MAX_SPEED_BONUS * (1 - seconds / limit))


def score_answer(question_type, is_correct, seconds):
    """Returns (points, bonus) for one answer."""
    if not is_correct:
        return 0, 0
    bonus = speed_bonus(question_type, seconds)
    return BASE_POINTS + bonus, bonus


# --------------------------------------------------------------------- badges

# code -> emoji
BADGES = {
    "subject_bronze": "🥉",
    "subject_silver": "🥈",
    "subject_gold": "🥇",
    "perfect": "💯",
    "speed": "⚡",
    "topic_master": "🎯",
}

# Subject level badges: code -> (tests needed, minimum percentage in each)
SUBJECT_LEVELS = [
    ("subject_bronze", 1, 70),
    ("subject_silver", 3, 80),
    ("subject_gold", 5, 90),
]
TOPIC_MASTER_PCT = 90
SPEED_MIN_PCT = 80
SPEED_MIN_SHARE = 0.6  # share of the maximum possible speed bonus


def _award(user, code, session, subject=None, teacher_test=None):
    exists = Badge.objects.filter(user=user, code=code, subject=subject, teacher_test=teacher_test).exists()
    if exists:
        return None
    return Badge.objects.create(user=user, code=code, subject=subject, teacher_test=teacher_test, session=session)


def award_badges(session):
    """Checks every badge rule after `session` was completed and returns the newly earned badges."""
    user, subject = session.user, session.subject
    earned = []

    completed = TestSession.objects.filter(user=user, subject=subject, status=TestSession.STATUS_COMPLETED)
    percentages = [s.percentage for s in completed]
    for code, needed, min_pct in SUBJECT_LEVELS:
        if sum(1 for pct in percentages if pct >= min_pct) >= needed:
            earned.append(_award(user, code, session, subject=subject))

    if session.total_questions and session.score == session.total_questions:
        earned.append(_award(user, "perfect", session, subject=subject))

    max_bonus = session.score * MAX_SPEED_BONUS
    if session.percentage >= SPEED_MIN_PCT and max_bonus and session.speed_bonus >= SPEED_MIN_SHARE * max_bonus:
        earned.append(_award(user, "speed", session, subject=subject))

    if session.teacher_test_id and session.percentage >= TOPIC_MASTER_PCT:
        earned.append(_award(user, "topic_master", session, teacher_test=session.teacher_test))

    return [badge for badge in earned if badge is not None]


def badge_label(badge, t, subject_display=""):
    """Human-readable name for a badge in the active language."""
    name = t.get(f"badge_{badge.code}", badge.code)
    if badge.teacher_test_id:
        return f"{name}: {badge.teacher_test.title}"
    if subject_display:
        return f"{name} · {subject_display}"
    return name


# --------------------------------------------------------------- leaderboard

def class_members(user):
    """The students ranked together with `user`: a teacher's roster, or a student's classmates."""
    profile = getattr(user, "profile", None)
    if profile is None:
        return Profile.objects.none()
    teacher = user if profile.role in (Profile.ROLE_TEACHER, Profile.ROLE_ADMIN) else profile.created_by
    if teacher is None:
        return Profile.objects.filter(user=user)
    return Profile.objects.filter(created_by=teacher, role=Profile.ROLE_STUDENT, user__is_active=True)


def leaderboard(user, since=None):
    """Rows of {user, points, tests, badges, rank}, best first."""
    members = list(class_members(user).select_related("user"))
    ids = [p.user_id for p in members]

    # Separate aggregates: summing session points in the same query as
    # counting badges would join the two tables and multiply the sums.
    sessions = TestSession.objects.filter(user_id__in=ids, status=TestSession.STATUS_COMPLETED)
    if since is not None:
        sessions = sessions.filter(completed_at__gte=since)
    totals = {
        row["user_id"]: row
        for row in sessions.values("user_id").annotate(total=Sum("points"), tests=Count("id"))
    }
    badge_counts = dict(
        Badge.objects.filter(user_id__in=ids).values("user_id").annotate(n=Count("id")).values_list("user_id", "n")
    )

    ranked = sorted(
        (
            {
                "user": p.user,
                "points": totals.get(p.user_id, {}).get("total") or 0,
                "tests": totals.get(p.user_id, {}).get("tests", 0),
                "badges": badge_counts.get(p.user_id, 0),
            }
            for p in members
        ),
        key=lambda r: (-r["points"], -r["badges"], r["user"].username),
    )
    for position, row in enumerate(ranked, start=1):
        row["rank"] = position
    return ranked
