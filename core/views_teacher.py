from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from core.decorators import role_required
from core.forms import CreateAccountForm
from core.i18n import DEFAULT_LANGUAGE, get_strings, subject_name
from core.models import (
    Assignment, DIFFICULTY_CHOICES, Profile, Question, Subject,
    TeacherQuestion, TeacherTest, TestSession,
)
from core.question_types import ALL_TYPES, ICONS
from core.services.document_parsing import ExtractionError, extract_text
from core.services.openrouter import GenerationError, parse_document_to_questions
from core.services.template_parser import TemplateParseError, parse_template


def _current_language(request):
    return request.session.get("language", DEFAULT_LANGUAGE)


def _roster(teacher):
    return (
        Profile.objects.filter(created_by=teacher, role=Profile.ROLE_STUDENT, user__is_active=True)
        .select_related("user")
    )


@role_required(Profile.ROLE_TEACHER)
def teacher_dashboard(request):
    roster = []
    for profile in _roster(request.user):
        sessions = list(TestSession.objects.filter(user=profile.user, status=TestSession.STATUS_COMPLETED))
        count = len(sessions)
        avg = round(sum(s.percentage for s in sessions) / count) if count else None
        roster.append({"user": profile.user, "attempts": count, "avg_pct": avg})

    tests = TeacherTest.objects.filter(teacher=request.user).select_related("subject")
    return render(request, "teacher/dashboard.html", {"roster": roster, "tests": tests})


@role_required(Profile.ROLE_TEACHER)
def add_student(request):
    if request.method == "POST":
        form = CreateAccountForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user, role=Profile.ROLE_STUDENT, created_by=request.user)
            messages.success(request, f"Student account '{user.username}' created.")
            return redirect("teacher_dashboard")
    else:
        form = CreateAccountForm()
    return render(request, "teacher/add_student.html", {"form": form})


@role_required(Profile.ROLE_TEACHER)
def remove_student(request, user_id):
    profile = get_object_or_404(Profile, user_id=user_id, created_by=request.user, role=Profile.ROLE_STUDENT)
    if request.method == "POST":
        profile.user.is_active = False
        profile.user.save(update_fields=["is_active"])
        messages.info(request, f"Removed {profile.user.username} — their history is kept but they can no longer log in.")
    return redirect("teacher_dashboard")


@role_required(Profile.ROLE_TEACHER)
def upload_test(request):
    lang = _current_language(request)
    t = get_strings(lang)
    subjects = Subject.objects.all()
    interaction_types = [
        {"code": code, "label": t[f"type_label_{code}"], "icon": ICONS[code]} for code in ALL_TYPES
    ]

    if request.method == "POST":
        subject = Subject.objects.filter(id=request.POST.get("subject")).first()
        title = request.POST.get("title", "").strip()
        difficulty = request.POST.get("difficulty") or None
        if difficulty not in [code for code, _ in DIFFICULTY_CHOICES]:
            difficulty = None
        mode = request.POST.get("mode")
        uploaded = request.FILES.get("file")
        chosen_types = [c for c in request.POST.getlist("interaction_types") if c in ALL_TYPES]

        error = None
        if mode not in ("template", "ai"):
            error = "Please choose a parsing mode."
        elif not subject or not title or not uploaded:
            error = "Please fill in subject, title, and choose a file."
        elif mode == "ai" and len(chosen_types) < 2:
            error = "Pick at least 2 interactive formats for AI parsing."

        parsed = None
        source = None
        if not error:
            try:
                raw_text = extract_text(uploaded)
            except ExtractionError as exc:
                error = str(exc)

        if not error:
            try:
                if mode == "template":
                    parsed = parse_template(raw_text)
                    source = TeacherTest.SOURCE_TEMPLATE_PARSED
                else:
                    parsed = parse_document_to_questions(raw_text, subject.name, chosen_types, lang)
                    source = TeacherTest.SOURCE_AI_PARSED
            except (TemplateParseError, GenerationError) as exc:
                error = str(exc)

        if error:
            messages.error(request, error)
        else:
            with transaction.atomic():
                teacher_test = TeacherTest.objects.create(
                    teacher=request.user,
                    subject=subject,
                    title=title,
                    difficulty=difficulty,
                    source=source,
                    language=lang,
                )
                for i, q in enumerate(parsed, start=1):
                    TeacherQuestion.objects.create(
                        teacher_test=teacher_test,
                        order=i,
                        type=q["type"],
                        prompt=q["prompt"],
                        data=q,
                        explanation=q.get("explanation", ""),
                    )
            messages.success(request, f"Uploaded {len(parsed)} question(s).")
            return redirect("teacher_test_assign", test_id=teacher_test.id)

    return render(
        request,
        "teacher/upload_test.html",
        {"subjects": subjects, "interaction_types": interaction_types, "difficulties": DIFFICULTY_CHOICES},
    )


@role_required(Profile.ROLE_TEACHER)
def assign_test(request, test_id):
    teacher_test = get_object_or_404(TeacherTest, id=test_id, teacher=request.user)
    students = _roster(request.user)

    if request.method == "POST":
        chosen_ids = request.POST.getlist("students")
        template_questions = list(teacher_test.questions.all())
        # Don't create a second concurrent pending attempt for someone who
        # already has one outstanding for this same test.
        already_pending = set(
            teacher_test.assignments.filter(test_session__status=TestSession.STATUS_READY)
            .values_list("student_id", flat=True)
        )
        assigned_count = 0
        with transaction.atomic():
            for profile in students.filter(user_id__in=chosen_ids).exclude(user_id__in=already_pending):
                session = TestSession.objects.create(
                    user=profile.user,
                    subject=teacher_test.subject,
                    requested_count=len(template_questions),
                    interaction_types=sorted({q.type for q in template_questions}),
                    language=teacher_test.language,
                    difficulty=teacher_test.difficulty,
                    status=TestSession.STATUS_READY,
                    source=TestSession.SOURCE_TEACHER,
                    teacher_test=teacher_test,
                    total_questions=len(template_questions),
                )
                for q in template_questions:
                    Question.objects.create(
                        session=session,
                        order=q.order,
                        type=q.type,
                        prompt=q.prompt,
                        data=q.data,
                        explanation=q.explanation,
                    )
                Assignment.objects.create(teacher_test=teacher_test, student=profile.user, test_session=session)
                assigned_count += 1
        messages.success(request, f"Assigned to {assigned_count} student(s).")
        return redirect("teacher_dashboard")

    already_assigned = set(
        teacher_test.assignments.filter(test_session__status=TestSession.STATUS_READY)
        .values_list("student_id", flat=True)
    )
    return render(
        request,
        "teacher/assign_test.html",
        {"teacher_test": teacher_test, "students": students, "already_assigned": already_assigned},
    )


@role_required(Profile.ROLE_TEACHER)
def test_results(request, test_id):
    teacher_test = get_object_or_404(TeacherTest, id=test_id, teacher=request.user)
    assignments = teacher_test.assignments.select_related("student", "test_session")
    return render(request, "teacher/test_results.html", {"teacher_test": teacher_test, "assignments": assignments})
