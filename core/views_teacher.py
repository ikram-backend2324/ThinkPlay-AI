from django.contrib import messages
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core import scaffold
from core.decorators import role_required
from core.forms import CreateAccountForm
from core.i18n import DEFAULT_LANGUAGE, get_strings, subject_name
from core.models import (
    Assignment, Badge, DIFFICULTY_CHOICES, Lecture, LessonPlan, Profile, Question, Subject,
    TeacherQuestion, TeacherTest, TestSession,
)
from core.question_types import ALL_TYPES, ICONS
from core.services.document_parsing import ExtractionError, extract_text
from core.services.openrouter import (
    GenerationError, design_lesson, generate_questions, parse_document_to_questions,
)
from core.services.template_parser import TemplateParseError, parse_template

TEACHER_ROLES = (Profile.ROLE_TEACHER, Profile.ROLE_ADMIN)
MIN_GENERATED = 3
MAX_GENERATED = 40
MAX_LECTURE_CHARS = 60000


def _current_language(request):
    return request.session.get("language", DEFAULT_LANGUAGE)


def _roster(teacher):
    return (
        Profile.objects.filter(created_by=teacher, role=Profile.ROLE_STUDENT, user__is_active=True)
        .select_related("user")
    )


def _subjects(lang):
    return [{"id": s.id, "icon": s.icon, "name": subject_name(s, lang)} for s in Subject.objects.all()]


def _interaction_types(t):
    return [{"code": code, "label": t[f"type_label_{code}"], "icon": ICONS[code]} for code in ALL_TYPES]


def _difficulties(t):
    return [(code, t[f"difficulty_{code}"]) for code, _ in DIFFICULTY_CHOICES]


def _clean_difficulty(value):
    return value if value in [code for code, _ in DIFFICULTY_CHOICES] else None


def _save_teacher_test(teacher, subject, title, difficulty, source, lang, questions):
    with transaction.atomic():
        teacher_test = TeacherTest.objects.create(
            teacher=teacher, subject=subject, title=title[:120], difficulty=difficulty, source=source, language=lang,
        )
        TeacherQuestion.objects.bulk_create(
            TeacherQuestion(
                teacher_test=teacher_test,
                order=i,
                type=q["type"],
                prompt=q["prompt"],
                data=q,
                explanation=q.get("explanation", ""),
            )
            for i, q in enumerate(questions, start=1)
        )
    return teacher_test


@role_required(*TEACHER_ROLES)
def teacher_dashboard(request):
    lang = _current_language(request)
    profiles = list(_roster(request.user))
    ids = [p.user_id for p in profiles]
    # One query for every student's sessions instead of one query per student.
    per_user = {uid: [] for uid in ids}
    for session in TestSession.objects.filter(user_id__in=ids, status=TestSession.STATUS_COMPLETED).only(
        "user_id", "score", "total_questions", "points"
    ):
        per_user[session.user_id].append(session)
    badge_counts = dict(
        Badge.objects.filter(user_id__in=ids).values("user_id").annotate(n=Count("id")).values_list("user_id", "n")
    )
    roster = []
    for profile in profiles:
        sessions = per_user[profile.user_id]
        count = len(sessions)
        roster.append({
            "user": profile.user,
            "attempts": count,
            "avg_pct": round(sum(s.percentage for s in sessions) / count) if count else None,
            "points": sum(s.points for s in sessions),
            "badges": badge_counts.get(profile.user_id, 0),
        })

    tests = [
        {"test": t, "subject_display": subject_name(t.subject, lang)}
        for t in TeacherTest.objects.filter(teacher=request.user).select_related("subject")
    ]
    plans = LessonPlan.objects.filter(teacher=request.user)[:5]
    return render(request, "teacher/dashboard.html", {"roster": roster, "tests": tests, "plans": plans})


@role_required(*TEACHER_ROLES)
def add_student(request):
    if request.method == "POST":
        form = CreateAccountForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user, role=Profile.ROLE_STUDENT, created_by=request.user)
            messages.success(request, get_strings(_current_language(request))["msg_student_created"].format(username=user.username))
            return redirect("teacher_dashboard")
    else:
        form = CreateAccountForm()
    return render(request, "teacher/add_student.html", {"form": form})


@role_required(*TEACHER_ROLES)
def remove_student(request, user_id):
    profile = get_object_or_404(Profile, user_id=user_id, created_by=request.user, role=Profile.ROLE_STUDENT)
    if request.method == "POST":
        profile.user.is_active = False
        profile.user.save(update_fields=["is_active"])
        messages.info(
            request,
            get_strings(_current_language(request))["msg_student_removed"].format(username=profile.user.username),
        )
    return redirect("teacher_dashboard")


@role_required(*TEACHER_ROLES)
def upload_test(request):
    lang = _current_language(request)
    t = get_strings(lang)

    if request.method == "POST":
        subject = Subject.objects.from_form(request.POST.get("subject"))
        title = request.POST.get("title", "").strip()
        difficulty = _clean_difficulty(request.POST.get("difficulty"))
        mode = request.POST.get("mode")
        uploaded = request.FILES.get("file")
        chosen_types = [c for c in request.POST.getlist("interaction_types") if c in ALL_TYPES]

        error = None
        if mode not in ("template", "ai"):
            error = t["msg_choose_parse_mode"]
        elif not subject or not title or not uploaded:
            error = t["msg_upload_fill_required"]
        elif mode == "ai" and len(chosen_types) < 2:
            error = t["msg_upload_ai_min_types"]

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
            teacher_test = _save_teacher_test(request.user, subject, title, difficulty, source, lang, parsed)
            messages.success(request, t["msg_upload_success"].format(count=len(parsed)))
            return redirect("teacher_test_assign", test_id=teacher_test.id)

    return render(
        request,
        "teacher/upload_test.html",
        {"subjects": _subjects(lang), "interaction_types": _interaction_types(t), "difficulties": _difficulties(t)},
    )


@role_required(*TEACHER_ROLES)
def assign_test(request, test_id):
    teacher_test = get_object_or_404(TeacherTest.objects.select_related("subject"), id=test_id, teacher=request.user)
    students = _roster(request.user)
    t = get_strings(_current_language(request))

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
                Question.objects.bulk_create(
                    Question(
                        session=session,
                        order=q.order,
                        type=q.type,
                        prompt=q.prompt,
                        data=q.data,
                        explanation=q.explanation,
                    )
                    for q in template_questions
                )
                Assignment.objects.create(teacher_test=teacher_test, student=profile.user, test_session=session)
                assigned_count += 1
        messages.success(request, t["msg_assign_success"].format(count=assigned_count))
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


@role_required(*TEACHER_ROLES)
def test_results(request, test_id):
    teacher_test = get_object_or_404(TeacherTest.objects.select_related("subject"), id=test_id, teacher=request.user)
    assignments = teacher_test.assignments.select_related("student", "test_session")
    return render(request, "teacher/test_results.html", {"teacher_test": teacher_test, "assignments": assignments})


# ------------------------------------------------------------------ lectures

@role_required(*TEACHER_ROLES)
def lectures(request):
    lang = _current_language(request)
    t = get_strings(lang)

    if request.method == "POST":
        subject = Subject.objects.from_form(request.POST.get("subject"))
        title = request.POST.get("title", "").strip()
        text = request.POST.get("text", "").strip()
        uploaded = request.FILES.get("file")

        error = None
        if not subject or not title or not (text or uploaded):
            error = t["msg_lecture_fill_required"]
        elif uploaded:
            try:
                text = extract_text(uploaded)
            except ExtractionError as exc:
                error = str(exc)

        if error:
            messages.error(request, error)
        else:
            lecture = Lecture.objects.create(
                teacher=request.user, subject=subject, title=title[:160], text=text[:MAX_LECTURE_CHARS]
            )
            messages.success(request, t["msg_lecture_saved"])
            return redirect("teacher_lecture_test", lecture_id=lecture.id)

    rows = [
        {"lecture": lec, "subject_display": subject_name(lec.subject, lang)}
        for lec in Lecture.objects.filter(teacher=request.user).select_related("subject")
    ]
    return render(request, "teacher/lectures.html", {"rows": rows, "subjects": _subjects(lang)})


@role_required(*TEACHER_ROLES)
@require_POST
def delete_lecture(request, lecture_id):
    lecture = get_object_or_404(Lecture, id=lecture_id, teacher=request.user)
    lecture.delete()
    messages.info(request, get_strings(_current_language(request))["msg_lecture_deleted"])
    return redirect("teacher_lectures")


def _generate_test_view(
    request, *, template, context, subject, default_title, source, topic=None, source_text=None, skip_post=False
):
    """Shared form handling for "make a test from a lecture / lesson plan / topic"."""
    lang = _current_language(request)
    t = get_strings(lang)

    if request.method == "POST" and not skip_post:
        chosen_types = [c for c in request.POST.getlist("interaction_types") if c in ALL_TYPES]
        difficulty = _clean_difficulty(request.POST.get("difficulty"))
        title = request.POST.get("title", "").strip() or default_title
        try:
            count = int(request.POST.get("count", 10))
        except (TypeError, ValueError):
            count = 0

        error = None
        if len(chosen_types) < 2:
            error = t["msg_min_types"]
        elif not MIN_GENERATED <= count <= MAX_GENERATED:
            error = t["msg_count_range"].format(min=MIN_GENERATED, max=MAX_GENERATED)

        if not error:
            try:
                questions = generate_questions(
                    subject_name=subject_name(subject, lang),
                    interaction_types=chosen_types,
                    count=count,
                    language=lang,
                    difficulty=difficulty,
                    topic=topic,
                    source_text=source_text,
                )
            except GenerationError:
                error = t["generating_failed_body"]

        if error:
            messages.error(request, error)
        else:
            teacher_test = _save_teacher_test(request.user, subject, title, difficulty, source, lang, questions)
            messages.success(request, t["msg_upload_success"].format(count=len(questions)))
            return redirect("teacher_test_assign", test_id=teacher_test.id)

    return render(
        request,
        template,
        {
            **context,
            "interaction_types": _interaction_types(t),
            "difficulties": _difficulties(t),
            "default_title": default_title,
            "min_count": MIN_GENERATED,
            "max_count": MAX_GENERATED,
        },
    )


@role_required(*TEACHER_ROLES)
def lecture_test(request, lecture_id):
    lecture = get_object_or_404(Lecture.objects.select_related("subject"), id=lecture_id, teacher=request.user)
    return _generate_test_view(
        request,
        template="teacher/generate_test.html",
        context={"lecture": lecture},
        subject=lecture.subject,
        default_title=lecture.title,
        source_text=lecture.text,
        source=TeacherTest.SOURCE_AI_LECTURE,
    )


@role_required(*TEACHER_ROLES)
def topic_test(request):
    """A test on any topic, written by the AI from its general knowledge (no lecture needed)."""
    lang = _current_language(request)
    subject = Subject.objects.from_form(request.POST.get("subject")) if request.method == "POST" else None
    topic = request.POST.get("topic", "").strip()[:200] if request.method == "POST" else ""
    context = {"subjects": _subjects(lang), "topic_mode": True, "topic": topic, "selected_subject": subject.id if subject else None}
    incomplete = request.method == "POST" and (not subject or not topic)
    if incomplete:
        messages.error(request, get_strings(lang)["msg_topic_fill_required"])
    return _generate_test_view(
        request,
        template="teacher/generate_test.html",
        context=context,
        subject=subject,
        default_title=topic,
        topic=topic,
        source=TeacherTest.SOURCE_AI_TOPIC,
        skip_post=incomplete,
    )


# ------------------------------------------------------ SCAFFOLD lesson plans

SETTING_KEYS = [card["code"] for card in scaffold.SETTING_CARDS]


@role_required(*TEACHER_ROLES)
def lesson_plans(request):
    plans = LessonPlan.objects.filter(teacher=request.user).select_related("subject")
    return render(request, "teacher/lesson_plans.html", {"plans": plans})


@role_required(*TEACHER_ROLES)
def lesson_plan_new(request):
    lang = _current_language(request)
    t = get_strings(lang)
    sc = scaffold.localized(lang)
    form = {"topic": "", "subject": "", "competences": [], "transversal": [], "method": "", "assessments": []}
    form.update({key: "" for key in SETTING_KEYS})

    if request.method == "POST":
        form = {
            "topic": request.POST.get("topic", "").strip()[:200],
            "subject": request.POST.get("subject", ""),
            "competences": [c for c in request.POST.getlist("competences") if c in scaffold.COMPETENCES],
            "transversal": [c for c in request.POST.getlist("transversal") if c in scaffold.TRANSVERSAL_BY_CODE],
            "method": request.POST.get("method", ""),
            "assessments": [a for a in request.POST.getlist("assessments") if a in scaffold.ASSESSMENTS_BY_CODE],
            **{key: request.POST.get(key, "").strip()[:500] for key in SETTING_KEYS},
        }
        subject = Subject.objects.from_form(form["subject"])
        use_ai = request.POST.get("use_ai") == "1"

        error = None
        if not form["topic"]:
            error = t["msg_plan_topic_required"]
        elif not form["competences"]:
            error = t["msg_plan_competences_required"]
        elif not use_ai and form["method"] not in scaffold.METHODS_BY_CODE:
            error = t["msg_plan_method_required"]

        plan, ai_generated = None, False
        if not error and use_ai:
            setting_for_ai = {
                "topic": form["topic"],
                "subject": subject.name if subject else "",
                **{key: form[key] for key in SETTING_KEYS},
                "transversal focus": ", ".join(scaffold.TRANSVERSAL_BY_CODE[c]["title"]["en"] for c in form["transversal"]),
                "teacher's preferred teaching method": (
                    scaffold.METHODS_BY_CODE[form["method"]]["title"]["en"] if form["method"] in scaffold.METHODS_BY_CODE else ""
                ),
            }
            competences = [scaffold.COMPETENCES[c]["title"]["en"] for c in form["competences"]]
            try:
                plan = design_lesson(setting_for_ai, competences, lang)
                ai_generated = True
            except GenerationError:
                if form["method"] in scaffold.METHODS_BY_CODE:
                    messages.warning(request, t["msg_plan_ai_failed_manual"])
                else:
                    error = t["msg_plan_ai_failed"]

        if not error and plan is None:
            plan = _manual_plan(form)

        if error:
            messages.error(request, error)
        else:
            lesson = LessonPlan.objects.create(
                teacher=request.user,
                subject=subject,
                topic=form["topic"],
                language=lang,
                setting={key: form[key] for key in ["competences", "transversal", *SETTING_KEYS]},
                plan=plan,
                ai_generated=ai_generated,
            )
            return redirect("teacher_lesson_plan", plan_id=lesson.id)

    setting_fields = [{**card, "value": form.get(card["code"], "")} for card in sc["setting_cards"]]
    return render(
        request,
        "teacher/lesson_plan_new.html",
        {"sc": sc, "subjects": _subjects(lang), "form": form, "setting_fields": setting_fields},
    )


def _manual_plan(form):
    """A plan built from the teacher's own card choices, used without AI. Its steps are
    left empty: the detail page shows the method card's steps in the viewer's language."""
    method = scaffold.METHODS_BY_CODE[form["method"]]
    return {
        "learning_outcomes": [],
        "teaching_method": {"code": method["code"], "why": ""},
        "steps": [],
        "diagnostic_assessment": None,
        "output": "",
        "final_assessment": [{"code": code, "how": ""} for code in form["assessments"]],
        "resources": [form["resources"]] if form.get("resources") else [],
        "timeline": [],
        "principles": [p["code"] for p in scaffold.PRINCIPLES if p["try_method"] == method["code"]],
        "quiz_topic": form["topic"],
    }


def _plan_context(plan_obj, lang):
    """Resolves the codes stored in a plan into localized cards for display."""
    plan = plan_obj.plan
    method = scaffold.METHODS_BY_CODE.get((plan.get("teaching_method") or {}).get("code"))

    def assessment(entry):
        if not entry or entry.get("code") not in scaffold.ASSESSMENTS_BY_CODE:
            return None
        card = scaffold.ASSESSMENTS_BY_CODE[entry["code"]]
        return {"title": scaffold.tr(card["title"], lang), "how": entry.get("how", ""),
                "hints": scaffold.tr(card["hints"], lang)}

    competences = [
        {"code": code, "title": scaffold.tr(scaffold.COMPETENCES[code]["title"], lang)}
        for code in plan_obj.setting.get("competences", []) if code in scaffold.COMPETENCES
    ]
    transversal = [
        scaffold.tr(scaffold.TRANSVERSAL_BY_CODE[c]["title"], lang)
        for c in plan_obj.setting.get("transversal", []) if c in scaffold.TRANSVERSAL_BY_CODE
    ]
    settings_rows = [
        {"title": scaffold.tr(card["title"], lang), "value": plan_obj.setting.get(card["code"], "")}
        for card in scaffold.SETTING_CARDS if plan_obj.setting.get(card["code"])
    ]
    # AI plans carry steps written for this lesson; card-based plans show the card's own steps.
    steps = plan.get("steps") or (scaffold.tr(method["steps"], lang) if method else [])
    return {
        "lesson": plan_obj,
        "plan": plan,
        "steps": steps,
        "method": {"title": scaffold.tr(method["title"], lang), "description": scaffold.tr(method["description"], lang),
                   "abbr": method["abbr"], "why": plan["teaching_method"].get("why", "")} if method else None,
        "diagnostic": assessment(plan.get("diagnostic_assessment")),
        "final": [a for a in (assessment(e) for e in plan.get("final_assessment", [])) if a],
        "principles": [scaffold.tr(scaffold.PRINCIPLES_BY_CODE[p]["title"], lang)
                       for p in plan.get("principles", []) if p in scaffold.PRINCIPLES_BY_CODE],
        "competences": competences,
        "transversal": transversal,
        "settings_rows": settings_rows,
        "total_minutes": sum(row.get("minutes", 0) for row in plan.get("timeline", [])),
    }


@role_required(*TEACHER_ROLES)
def lesson_plan_detail(request, plan_id):
    lesson = get_object_or_404(LessonPlan.objects.select_related("subject"), id=plan_id, teacher=request.user)
    return render(request, "teacher/lesson_plan_detail.html", _plan_context(lesson, _current_language(request)))


@role_required(*TEACHER_ROLES)
@require_POST
def lesson_plan_delete(request, plan_id):
    get_object_or_404(LessonPlan, id=plan_id, teacher=request.user).delete()
    messages.info(request, get_strings(_current_language(request))["msg_plan_deleted"])
    return redirect("teacher_lesson_plans")


@role_required(*TEACHER_ROLES)
def lesson_plan_test(request, plan_id):
    lesson = get_object_or_404(LessonPlan.objects.select_related("subject"), id=plan_id, teacher=request.user)
    lang = _current_language(request)
    subject = lesson.subject or Subject.objects.first()
    topic = lesson.plan.get("quiz_topic") or lesson.topic
    return _generate_test_view(
        request,
        template="teacher/generate_test.html",
        context={"lesson": lesson, "topic": topic, "subject_display": subject_name(subject, lang)},
        subject=subject,
        default_title=lesson.topic,
        topic=topic,
        source=TeacherTest.SOURCE_AI_TOPIC,
    )
