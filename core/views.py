import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.forms import RegisterForm
from core.grading import grade_answer
from core.models import Answer, Question, Subject, TestSession
from core.question_types import ALL_TYPES, DESCRIPTIONS, ICONS, LABELS
from core.review import describe_answer
from core.services.openrouter import GenerationError, generate_question_batch

MIN_QUESTIONS = 10
MAX_QUESTIONS = 100


def landing(request):
    return render(request, "landing.html")


def register(request):
    if request.user.is_authenticated:
        return redirect("quiz_setup")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, f"Welcome, {user.username}!")
            return redirect("quiz_setup")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


class ThemedLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


login_view = ThemedLoginView.as_view()


def logout_view(request):
    auth_logout(request)
    messages.info(request, "You've been logged out.")
    return redirect("landing")


@login_required
def history(request):
    sessions = (
        TestSession.objects.filter(user=request.user, status=TestSession.STATUS_COMPLETED)
        .select_related("subject")
    )
    return render(request, "accounts/history.html", {"sessions": sessions})


@login_required
def quiz_setup(request):
    subjects = Subject.objects.all()
    interaction_types = [
        {"code": code, "label": LABELS[code], "description": DESCRIPTIONS[code], "icon": ICONS[code]}
        for code in ALL_TYPES
    ]

    if request.method == "POST":
        subject_id = request.POST.get("subject")
        count = request.POST.get("count")
        chosen_types = request.POST.getlist("interaction_types")

        subject = Subject.objects.filter(id=subject_id).first()
        try:
            count = int(count)
        except (TypeError, ValueError):
            count = 0
        chosen_types = [t for t in chosen_types if t in ALL_TYPES]

        error = None
        if not subject:
            error = "Please choose a subject."
        elif not (MIN_QUESTIONS <= count <= MAX_QUESTIONS):
            error = f"Question count must be between {MIN_QUESTIONS} and {MAX_QUESTIONS}."
        elif len(chosen_types) < 2:
            error = "Pick at least 2 interactive question formats."

        if error:
            messages.error(request, error)
        else:
            session = TestSession.objects.create(
                user=request.user,
                subject=subject,
                requested_count=count,
                interaction_types=chosen_types,
                status=TestSession.STATUS_GENERATING,
            )
            return redirect("quiz_generating", session_id=session.id)

    return render(
        request,
        "quiz/setup.html",
        {
            "subjects": subjects,
            "interaction_types": interaction_types,
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
            subject_name=session.subject.name,
            interaction_types=session.valid_interaction_types(),
            count=batch_size,
            avoid_topics=avoid_topics,
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
    rows = []
    for question in session.questions.select_related("answer").all():
        your_answer, correct_answer = describe_answer(
            question.type, question.data, question.answer.submitted_data
        )
        rows.append(
            {
                "question": question,
                "type_label": LABELS.get(question.type, question.type),
                "is_correct": question.answer.is_correct,
                "your_answer": your_answer,
                "correct_answer": correct_answer,
            }
        )
    return render(request, "quiz/review.html", {"session": session, "rows": rows})
