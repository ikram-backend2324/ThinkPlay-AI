import json
from collections import defaultdict

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

from core.grading import grade_answer
from core.i18n import DEFAULT_LANGUAGE, LANGUAGE_CODES, get_strings, subject_name
from core.models import Answer, DIFFICULTY_CODES, Profile, Question, Subject, TestSession
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

    return render(request, "accounts/history.html", {"sessions": sessions, "subject_stats": subject_stats})


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

        subject = Subject.objects.filter(id=subject_id).first()
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
    except (ValueError, TypeError):
        answers = {}

    questions = list(session.questions.all())
    score = 0
    answer_objs = []
    for question in questions:
        submitted = answers.get(str(question.id), {})
        is_correct = grade_answer(question.type, question.data, submitted)
        if is_correct:
            score += 1
        answer_objs.append(
            Answer(question=question, submitted_data=submitted, is_correct=is_correct)
        )

    with transaction.atomic():
        Answer.objects.filter(question__session=session).delete()
        Answer.objects.bulk_create(answer_objs)
        session.score = score
        session.total_questions = len(questions)
        session.status = TestSession.STATUS_COMPLETED
        session.completed_at = timezone.now()
        session.save(update_fields=["score", "total_questions", "status", "completed_at"])

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
    return render(request, "quiz/results.html", {"session": session})


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
