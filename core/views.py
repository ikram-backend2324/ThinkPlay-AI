import json
from collections import defaultdict
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from core import scaffold
from core.gamification import BADGES, award_badges, badge_label, clean_seconds, leaderboard, score_answer
from core.grading import grade_answer
from core.i18n import DEFAULT_LANGUAGE, LANGUAGE_CODES, get_strings, subject_name
from core.models import Answer, DIFFICULTY_CODES, Lecture, Profile, Question, Subject, TestSession
from core.question_types import ALL_TYPES, ICONS
from core.review import describe_answer
from core.services.openrouter import GenerationError, generate_question_batch

MIN_QUESTIONS = 10
MAX_QUESTIONS = 100


def _current_language(request):
    return request.session.get("language", DEFAULT_LANGUAGE)


def set_language_view(request):
    if request.method == "POST":
        lang = request.POST.get("language")
        next_url = request.POST.get("next") or "/"
        if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
            next_url = "/"
        if lang in LANGUAGE_CODES:
            request.session["language"] = lang
        return redirect(next_url)
    return redirect("landing")


def landing(request):
    return render(request, "landing.html")


class ThemedLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


login_view = ThemedLoginView.as_view()


@login_required
def post_login_redirect(request):
    """
    Closed system — no self-registration. Everyone lands on the main site
    (with its own nav, not Django admin's separate page shell) so admin can
    just as easily solve a test themselves as jump into /admin/ or
    /teacher/ — both are one click away in the nav for their role.
    """
    role = getattr(request.user, "profile", None) and request.user.profile.role
    if role == Profile.ROLE_TEACHER:
        return redirect("teacher_dashboard")
    return redirect("quiz_setup")


def logout_view(request):
    t = get_strings(_current_language(request))
    auth_logout(request)
    messages.info(request, t["msg_logged_out"])
    return redirect("landing")


@login_required
def history(request):
    lang = _current_language(request)
    sessions = list(
        TestSession.objects.filter(user=request.user, status=TestSession.STATUS_COMPLETED)
        .select_related("subject")
    )

    grouped = defaultdict(lambda: {"icon": "", "name": "", "pct_sum": 0, "attempts": 0})
    for s in sessions:
        g = grouped[s.subject_id]
        g["icon"] = s.subject.icon
        g["name"] = subject_name(s.subject, lang)
        g["pct_sum"] += s.percentage
        g["attempts"] += 1
    subject_stats = sorted(
        (
            {
                "icon": g["icon"],
                "name": g["name"],
                "attempts": g["attempts"],
                "avg_pct": round(g["pct_sum"] / g["attempts"]),
            }
            for g in grouped.values()
        ),
        key=lambda row: -row["avg_pct"],
    )

    t = get_strings(lang)
    badges = [
        {"emoji": BADGES.get(b.code, "🏅"), "label": badge_label(b, t, subject_name(b.subject, lang) if b.subject else "")}
        for b in request.user.badges.select_related("subject", "teacher_test")
    ]
    total_points = sum(s.points for s in sessions)
    return render(
        request,
        "accounts/history.html",
        {"sessions": sessions, "subject_stats": subject_stats, "badges": badges, "total_points": total_points},
    )


@login_required
def leaderboard_view(request):
    period = request.GET.get("period", "all")
    since = timezone.now() - timedelta(days=7) if period == "week" else None
    rows = leaderboard(request.user, since=since)
    return render(request, "accounts/leaderboard.html", {"rows": rows, "period": period})


def _teacher_of(user):
    """The teacher whose materials a user can see: themselves for teachers/admins, their creator for students."""
    profile = getattr(user, "profile", None)
    if profile is None:
        return None
    if profile.role in (Profile.ROLE_TEACHER, Profile.ROLE_ADMIN):
        return user
    return profile.created_by


@login_required
def materials(request):
    lang = _current_language(request)
    teacher = _teacher_of(request.user)
    lectures = Lecture.objects.filter(teacher=teacher).select_related("subject") if teacher else Lecture.objects.none()
    rows = [{"lecture": lec, "subject_display": subject_name(lec.subject, lang)} for lec in lectures]
    return render(request, "accounts/materials.html", {"rows": rows})


@login_required
def material_detail(request, lecture_id):
    lecture = get_object_or_404(Lecture, id=lecture_id, teacher=_teacher_of(request.user))
    paragraphs = [p.strip() for p in lecture.text.split("\n") if p.strip()]
    return render(request, "accounts/material_detail.html", {"lecture": lecture, "paragraphs": paragraphs})


# ------------------------------------------------------------ SCAFFOLD guide

def guide(request):
    lang = _current_language(request)
    return render(
        request,
        "guide/index.html",
        {"sc": scaffold.localized(lang), "source_title": scaffold.SOURCE_TITLE, "source_url": scaffold.SOURCE_URL,
         "license_url": scaffold.LICENSE_URL},
    )


# ------------------------------------------------------------- offline (PWA)

def service_worker(request):
    response = render(request, "pwa/sw.js", {"version": settings.PWA_CACHE_VERSION}, content_type="application/javascript")
    response["Cache-Control"] = "no-cache"
    return response


def manifest(request):
    return render(request, "pwa/manifest.webmanifest", {}, content_type="application/manifest+json")


def offline(request):
    return render(request, "pwa/offline.html")


@login_required
def assigned_tests(request):
    lang = _current_language(request)
    pending = (
        TestSession.objects.filter(
            user=request.user, source=TestSession.SOURCE_TEACHER, status=TestSession.STATUS_READY
        )
        .select_related("subject", "teacher_test", "teacher_test__teacher")
    )
    rows = [
        {
            "session": s,
            "subject_display": subject_name(s.subject, lang),
            "teacher_name": s.teacher_test.teacher.username if s.teacher_test else "",
        }
        for s in pending
    ]
    return render(request, "accounts/assigned.html", {"rows": rows})


@login_required
def quiz_setup(request):
    lang = _current_language(request)
    t = get_strings(lang)

    subjects = [
        {"id": s.id, "icon": s.icon, "name": subject_name(s, lang)}
        for s in Subject.objects.all()
    ]
    interaction_types = [
        {
            "code": code,
            "label": t[f"type_label_{code}"],
            "description": t[f"type_desc_{code}"],
            "icon": ICONS[code],
        }
        for code in ALL_TYPES
    ]
    difficulties = [
        {"code": code, "label": t[f"difficulty_{code}"]} for code in DIFFICULTY_CODES
    ]

    if request.method == "POST":
        subject_id = request.POST.get("subject")
        count = request.POST.get("count")
        chosen_types = request.POST.getlist("interaction_types")
        difficulty = request.POST.get("difficulty")

        subject = Subject.objects.from_form(subject_id)
        try:
            count = int(count)
        except (TypeError, ValueError):
            count = 0
        chosen_types = [ctype for ctype in chosen_types if ctype in ALL_TYPES]
        if difficulty not in DIFFICULTY_CODES:
            difficulty = None

        error = None
        if not subject:
            error = t["msg_choose_subject"]
        elif not (MIN_QUESTIONS <= count <= MAX_QUESTIONS):
            error = t["msg_count_range"].format(min=MIN_QUESTIONS, max=MAX_QUESTIONS)
        elif len(chosen_types) < 2:
            error = t["msg_min_types"]
        elif not difficulty:
            error = t["msg_choose_difficulty"]

        if error:
            messages.error(request, error)
        else:
            session = TestSession.objects.create(
                user=request.user,
                subject=subject,
                requested_count=count,
                interaction_types=chosen_types,
                language=lang,
                difficulty=difficulty,
                status=TestSession.STATUS_GENERATING,
            )
            return redirect("quiz_generating", session_id=session.id)

    return render(
        request,
        "quiz/setup.html",
        {
            "subjects": subjects,
            "interaction_types": interaction_types,
            "difficulties": difficulties,
            "min_questions": MIN_QUESTIONS,
            "max_questions": MAX_QUESTIONS,
        },
    )


@login_required
def quiz_generating(request, session_id):
    session = get_object_or_404(TestSession, id=session_id, user=request.user)
    if session.status == TestSession.STATUS_READY:
        return redirect("quiz_take", session_id=session.id)
    return render(request, "quiz/generating.html", {"session": session})


@login_required
@require_POST
def generate_batch(request, session_id):
    session = get_object_or_404(TestSession, id=session_id, user=request.user)

    if session.status != TestSession.STATUS_GENERATING:
        existing = session.questions.count()
        return JsonResponse({"generated": existing, "target": session.requested_count, "done": True})

    existing_count = session.questions.count()
    remaining = session.requested_count - existing_count
    if remaining <= 0:
        session.status = TestSession.STATUS_READY
        session.save(update_fields=["status"])
        return JsonResponse({"generated": existing_count, "target": session.requested_count, "done": True})

    batch_size = min(settings.QUESTION_BATCH_SIZE, remaining)
    avoid_topics = list(session.questions.values_list("prompt", flat=True))

    try:
        questions = generate_question_batch(
            subject_name=subject_name(session.subject, session.language),
            interaction_types=session.valid_interaction_types(),
            count=batch_size,
            avoid_topics=avoid_topics,
            language=session.language,
            difficulty=session.difficulty,
        )
    except GenerationError as exc:
        if existing_count == 0:
            session.status = TestSession.STATUS_FAILED
            session.save(update_fields=["status"])
            return JsonResponse({"error": str(exc), "done": True, "failed": True}, status=502)
        # We already have some questions — just stop early with what we've got.
        session.requested_count = existing_count
        session.status = TestSession.STATUS_READY
        session.save(update_fields=["requested_count", "status"])
        return JsonResponse({"generated": existing_count, "target": existing_count, "done": True})

    with transaction.atomic():
        order = existing_count
        for q in questions:
            order += 1
            Question.objects.create(
                session=session,
                order=order,
                type=q["type"],
                prompt=q["prompt"],
                data=q,
                explanation=q.get("explanation", ""),
            )

    new_total = session.questions.count()
    done = new_total >= session.requested_count
    if done:
        session.status = TestSession.STATUS_READY
        session.save(update_fields=["status"])

    return JsonResponse({"generated": new_total, "target": session.requested_count, "done": done})


@login_required
def quiz_take(request, session_id):
    session = get_object_or_404(TestSession, id=session_id, user=request.user)
    if session.status == TestSession.STATUS_GENERATING:
        return redirect("quiz_generating", session_id=session.id)
    if session.status == TestSession.STATUS_COMPLETED:
        return redirect("quiz_results", session_id=session.id)
    if session.status == TestSession.STATUS_ABANDONED:
        return redirect("quiz_setup")

    questions = list(session.questions.all().values("id", "order", "type", "data"))
    return render(
        request,
        "quiz/take.html",
        {"session": session, "questions": questions},
    )


@login_required
@require_POST
def quiz_submit(request, session_id):
    session = get_object_or_404(TestSession, id=session_id, user=request.user)
    if session.status == TestSession.STATUS_COMPLETED:
        return JsonResponse({"redirect": reverse_lazy("quiz_results", args=[session.id])})
    if session.status == TestSession.STATUS_ABANDONED:
        return JsonResponse({"redirect": reverse_lazy("quiz_setup")})

    try:
        payload = json.loads(request.body)
        answers = payload.get("answers", {})
    except (ValueError, TypeError, AttributeError):
        payload, answers = {}, {}

    times = payload.get("times", {}) if isinstance(payload, dict) else {}
    if not isinstance(answers, dict):
        answers = {}
    if not isinstance(times, dict):
        times = {}

    questions = list(session.questions.all())
    score = points = bonus_total = 0
    answer_objs = []
    for question in questions:
        submitted = answers.get(str(question.id), {})
        is_correct = grade_answer(question.type, question.data, submitted)
        seconds = clean_seconds(times.get(str(question.id)))
        earned, bonus = score_answer(question.type, is_correct, seconds)
        score += int(is_correct)
        points += earned
        bonus_total += bonus
        answer_objs.append(
            Answer(question=question, submitted_data=submitted, is_correct=is_correct, time_spent=seconds)
        )

    with transaction.atomic():
        Answer.objects.filter(question__session=session).delete()
        Answer.objects.bulk_create(answer_objs)
        session.score = score
        session.total_questions = len(questions)
        session.points = points
        session.speed_bonus = bonus_total
        session.status = TestSession.STATUS_COMPLETED
        session.completed_at = timezone.now()
        session.save(update_fields=["score", "total_questions", "points", "speed_bonus", "status", "completed_at"])
        award_badges(session)

    return JsonResponse({"redirect": reverse_lazy("quiz_results", args=[session.id])})


@login_required
@require_POST
def quiz_abandon(request, session_id):
    session = get_object_or_404(TestSession, id=session_id, user=request.user)
    if session.status not in (TestSession.STATUS_COMPLETED, TestSession.STATUS_ABANDONED):
        session.status = TestSession.STATUS_ABANDONED
        session.save(update_fields=["status"])
        t = get_strings(_current_language(request))
        messages.info(request, t["msg_test_abandoned"])
    return redirect("quiz_setup")


@login_required
def quiz_results(request, session_id):
    session = get_object_or_404(TestSession, id=session_id, user=request.user)
    if session.status != TestSession.STATUS_COMPLETED:
        return redirect("quiz_take", session_id=session.id)
    lang = _current_language(request)
    t = get_strings(lang)
    badges = [
        {"emoji": BADGES.get(b.code, "🏅"), "label": badge_label(b, t, subject_name(b.subject, lang) if b.subject else "")}
        for b in session.badges.select_related("subject", "teacher_test")
    ]
    return render(request, "quiz/results.html", {"session": session, "badges": badges})


@login_required
def quiz_review(request, session_id):
    session = get_object_or_404(TestSession, id=session_id, user=request.user)
    if session.status != TestSession.STATUS_COMPLETED:
        return redirect("quiz_take", session_id=session.id)
    t = get_strings(_current_language(request))
    rows = []
    for question in session.questions.select_related("answer").all():
        your_answer, correct_answer = describe_answer(
            question.type, question.data, question.answer.submitted_data, t
        )
        rows.append(
            {
                "question": question,
                "type_label": t.get(f"type_label_{question.type}", question.type),
                "is_correct": question.answer.is_correct,
                "your_answer": your_answer,
                "correct_answer": correct_answer,
            }
        )
    return render(request, "quiz/review.html", {"session": session, "rows": rows})
