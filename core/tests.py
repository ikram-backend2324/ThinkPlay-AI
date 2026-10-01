import json
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core import gamification, scaffold
from core.i18n import LANGUAGE_CODES, TRANSLATIONS, get_strings
from core.models import (
    Answer, Assignment, Badge, Lecture, LessonPlan, Profile, Question, Subject, TeacherQuestion, TeacherTest,
    TestSession,
)
from core.question_types import (
    CATEGORIZE, CODE_COMPLETE, FILL_BLANK, HOTSPOT_TEXT, MATCHING, MULTI_SELECT, NUMERIC, ORDERING,
)
from core.services.openrouter import GenerationError, validate_plan
from core.services.template_parser import TemplateParseError, parse_template


def make_user(username, role, created_by=None):
    user = User.objects.create_user(username, password="pass12345")
    Profile.objects.create(user=user, role=role, created_by=created_by)
    return user


FILL = {"type": FILL_BLANK, "prompt": "2 + 2 = ___", "accepted_answers": ["4"], "explanation": ""}
CHOICE = {"type": MULTI_SELECT, "prompt": "Pick 1", "options": [{"id": "a", "text": "1"}, {"id": "b", "text": "2"}],
          "correct_ids": ["a"], "explanation": ""}


def make_session(user, subject, questions=(FILL, CHOICE), status=TestSession.STATUS_READY, **extra):
    session = TestSession.objects.create(
        user=user, subject=subject, requested_count=len(questions), interaction_types=[q["type"] for q in questions],
        status=status, **extra,
    )
    for i, q in enumerate(questions, start=1):
        Question.objects.create(session=session, order=i, type=q["type"], prompt=q["prompt"], data=q)
    return session


# ------------------------------------------------------------ template parser

class TemplateParserTests(TestCase):
    def test_legacy_choice_format_still_works(self):
        qs = parse_template("Q1: Capital?\nA) London\nB) Paris\nCorrect: B\nExplanation: Paris.")
        self.assertEqual(qs[0]["type"], MULTI_SELECT)
        self.assertEqual(qs[0]["correct_ids"], ["b"])
        self.assertEqual(qs[0]["explanation"], "Paris.")

    def test_choice_with_several_correct_letters(self):
        qs = parse_template("Q: Primes?\nA) 2\nB) 4\nC) 7\nCorrect: A, C")
        self.assertEqual(qs[0]["correct_ids"], ["a", "c"])

    def test_every_interactive_format(self):
        text = """
Q: Water boils at ___ °C.
Type: fill_blank
Answer: 100 | yuz

Q: Match.
Type: matching
France = Paris
Japan -> Tokyo

Q: Order.
Type: ordering
1) one
2) two
3) three

Q: Right angle?
Type: numeric
Answer: 90
Tolerance: 0,5
Unit: °

Q: Sort.
Type: categorize
Mammals: Dog; Whale
Birds: Eagle

Q: Verbs.
Type: hotspot
Text: The cat [sat] and [purred].

Q: Loop.
Type: code
Language: python
Code:
for i in ___(5):
    print(i)
Answer: range
"""
        qs = parse_template(text)
        self.assertEqual(
            [q["type"] for q in qs],
            [FILL_BLANK, MATCHING, ORDERING, NUMERIC, CATEGORIZE, HOTSPOT_TEXT, CODE_COMPLETE],
        )
        fill, match, order, numeric, cat, hot, code = qs
        self.assertEqual(fill["accepted_answers"], ["100", "yuz"])
        self.assertEqual([p["right"] for p in match["pairs"]], ["Paris", "Tokyo"])
        self.assertEqual(order["correct_order"], ["1", "2", "3"])
        self.assertNotEqual([i["id"] for i in order["items"]], order["correct_order"])  # shuffled for display
        self.assertEqual((numeric["answer"], numeric["tolerance"], numeric["unit"]), (90, 0.5, "°"))
        self.assertLessEqual(numeric["min"], 90)
        self.assertGreaterEqual(numeric["max"], 90)
        self.assertEqual(len(cat["categories"]), 2)
        self.assertEqual(len(cat["items"]), 3)
        self.assertEqual([t["text"] for t in hot["tokens"] if t["id"] in hot["correct_ids"]], ["sat", "purred"])
        self.assertEqual(code["code_template"], "for i in ___(5):\n    print(i)")
        self.assertEqual(code["language"], "python")

    def test_uzbek_and_russian_keywords(self):
        qs = parse_template("Savol: Suv ___ da qaynaydi.\nTur: boʻsh joy\nJavob: 100\nIzoh: Normal bosimda.")
        self.assertEqual(qs[0]["type"], FILL_BLANK)
        self.assertEqual(qs[0]["explanation"], "Normal bosimda.")
        qs = parse_template("Вопрос: Столица?\nА) Москва\nБ) Ташкент\nОтвет: Б")
        self.assertEqual(qs[0]["correct_ids"], ["б"])

    def test_errors_are_explained(self):
        for text, fragment in [
            ("Q: x\nA) 1\nB) 2", "Correct"),
            ("Q: x\nA) 1\nCorrect: C", "option letters"),
            ("Q: no blank\nType: fill_blank\nAnswer: 1", "___"),
            ("Q: one pair\nType: matching\na = b", "2"),
            ("Q: x\nType: numeric\nAnswer: ten", "number"),
            ("Q: x\nType: wizardry", "unknown"),
            ("just text, no questions", "No questions"),
        ]:
            with self.subTest(text=text):
                with self.assertRaisesRegex(TemplateParseError, fragment):
                    parse_template(text)


# ---------------------------------------------------------------- gamification

class PointsTests(TestCase):
    def test_speed_bonus_shrinks_with_time(self):
        self.assertEqual(gamification.speed_bonus(FILL_BLANK, 0), gamification.speed_bonus(FILL_BLANK, 2))
        self.assertGreater(gamification.speed_bonus(FILL_BLANK, 5), gamification.speed_bonus(FILL_BLANK, 20))
        self.assertEqual(gamification.speed_bonus(FILL_BLANK, 30), 0)
        self.assertLessEqual(gamification.speed_bonus(MATCHING, 0), gamification.MAX_SPEED_BONUS)

    def test_wrong_answers_earn_nothing(self):
        self.assertEqual(gamification.score_answer(FILL_BLANK, False, 1), (0, 0))
        points, bonus = gamification.score_answer(FILL_BLANK, True, 3)
        self.assertEqual(points, gamification.BASE_POINTS + bonus)

    def test_clean_seconds_rejects_garbage(self):
        for value in [None, "abc", -5, float("nan")]:
            self.assertEqual(gamification.clean_seconds(value), 0.0)
        self.assertEqual(gamification.clean_seconds(10**9), 3600.0)


class SubmitAndBadgeTests(TestCase):
    def setUp(self):
        self.subject = Subject.objects.get(slug="math")
        self.teacher = make_user("teacher", Profile.ROLE_TEACHER)
        self.student = make_user("student", Profile.ROLE_STUDENT, created_by=self.teacher)
        self.client.force_login(self.student)

    def submit(self, session, answers, times=None):
        q1, q2 = session.questions.order_by("order")
        payload = {"answers": {str(q1.id): answers[0], str(q2.id): answers[1]}}
        if times is not None:
            payload["times"] = {str(q1.id): times[0], str(q2.id): times[1]}
        return self.client.post(
            reverse("quiz_submit", args=[session.id]), json.dumps(payload), content_type="application/json"
        )

    def test_points_bonus_and_badges(self):
        session = make_session(self.student, self.subject)
        response = self.submit(session, [{"value": "4"}, {"selected_ids": ["a"]}], times=[3, 4])
        self.assertEqual(response.status_code, 200)
        session.refresh_from_db()
        self.assertEqual((session.score, session.total_questions), (2, 2))
        self.assertGreater(session.speed_bonus, 0)
        self.assertEqual(session.points, 2 * gamification.BASE_POINTS + session.speed_bonus)
        codes = set(Badge.objects.filter(user=self.student).values_list("code", flat=True))
        self.assertTrue({"subject_bronze", "perfect", "speed"} <= codes)
        self.assertContains(self.client.get(reverse("quiz_results", args=[session.id])), "Bronze")

    def test_missing_times_still_grades(self):
        session = make_session(self.student, self.subject)
        self.submit(session, [{"value": "4"}, {"selected_ids": ["b"]}])
        session.refresh_from_db()
        self.assertEqual(session.score, 1)
        # A missing time counts as MIN_SECONDS, so it can never beat a genuinely fast answer.
        expected_bonus = gamification.speed_bonus(FILL_BLANK, gamification.MIN_SECONDS)
        self.assertEqual(session.speed_bonus, expected_bonus)
        self.assertEqual(session.points, gamification.BASE_POINTS + expected_bonus)

    def test_resubmission_is_ignored(self):
        session = make_session(self.student, self.subject)
        self.submit(session, [{"value": "4"}, {"selected_ids": ["a"]}])
        self.submit(session, [{"value": "0"}, {"selected_ids": []}])
        session.refresh_from_db()
        self.assertEqual(session.score, 2)

    def test_badges_are_not_duplicated(self):
        for _ in range(2):
            session = make_session(self.student, self.subject)
            self.submit(session, [{"value": "4"}, {"selected_ids": ["a"]}], times=[3, 3])
        self.assertEqual(Badge.objects.filter(user=self.student, code="subject_bronze").count(), 1)

    def test_topic_master_for_teacher_test(self):
        teacher_test = TeacherTest.objects.create(
            teacher=self.teacher, subject=self.subject, title="Fractions", source=TeacherTest.SOURCE_TEMPLATE_PARSED
        )
        session = make_session(self.student, self.subject, source=TestSession.SOURCE_TEACHER, teacher_test=teacher_test)
        self.submit(session, [{"value": "4"}, {"selected_ids": ["a"]}])
        self.assertTrue(Badge.objects.filter(user=self.student, code="topic_master", teacher_test=teacher_test).exists())

    def test_other_users_session_is_404(self):
        other = make_user("other", Profile.ROLE_STUDENT, created_by=self.teacher)
        session = make_session(other, self.subject)
        response = self.submit(session, [{"value": "4"}, {"selected_ids": ["a"]}])
        self.assertEqual(response.status_code, 404)


class LeaderboardTests(TestCase):
    def test_ranking_counts_points_once_per_session(self):
        subject = Subject.objects.get(slug="math")
        teacher = make_user("t", Profile.ROLE_TEACHER)
        alice = make_user("alice", Profile.ROLE_STUDENT, created_by=teacher)
        bob = make_user("bob", Profile.ROLE_STUDENT, created_by=teacher)
        outsider = make_user("eve", Profile.ROLE_STUDENT)
        for points in (100, 150):
            make_session(alice, subject, status=TestSession.STATUS_COMPLETED, points=points)
        make_session(bob, subject, status=TestSession.STATUS_COMPLETED, points=300)
        make_session(outsider, subject, status=TestSession.STATUS_COMPLETED, points=999)
        # Badges must not multiply the point sums.
        for code in ("subject_bronze", "perfect", "speed"):
            Badge.objects.create(user=alice, code=code, subject=subject)

        rows = gamification.leaderboard(alice)
        self.assertEqual([(r["user"].username, r["points"]) for r in rows], [("bob", 300), ("alice", 250)])
        self.assertEqual(rows[1]["badges"], 3)
        self.assertEqual(gamification.leaderboard(teacher), rows)


# ------------------------------------------------------------- access rules

class AccessTests(TestCase):
    def setUp(self):
        self.subject = Subject.objects.get(slug="math")
        self.teacher = make_user("teacher", Profile.ROLE_TEACHER)
        self.other_teacher = make_user("teacher2", Profile.ROLE_TEACHER)
        self.student = make_user("student", Profile.ROLE_STUDENT, created_by=self.teacher)
        self.lecture = Lecture.objects.create(teacher=self.teacher, subject=self.subject, title="L1", text="Text")
        self.plan = LessonPlan.objects.create(
            teacher=self.teacher, topic="T", plan={"teaching_method": {"code": "pbl"}}, setting={}
        )

    def test_student_cannot_open_teacher_pages(self):
        self.client.force_login(self.student)
        for name, args in [("teacher_dashboard", []), ("teacher_lectures", []), ("teacher_lesson_plans", []),
                           ("teacher_lesson_plan_new", []), ("teacher_topic_test", []),
                           ("teacher_lecture_test", [self.lecture.id])]:
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 403)

    def test_teachers_only_see_their_own_things(self):
        self.client.force_login(self.other_teacher)
        self.assertEqual(self.client.get(reverse("teacher_lecture_test", args=[self.lecture.id])).status_code, 404)
        self.assertEqual(self.client.get(reverse("teacher_lesson_plan", args=[self.plan.id])).status_code, 404)
        self.assertEqual(self.client.get(reverse("material_detail", args=[self.lecture.id])).status_code, 404)

    def test_student_reads_only_own_teachers_materials(self):
        self.client.force_login(self.student)
        self.assertContains(self.client.get(reverse("materials")), "L1")
        self.assertEqual(self.client.get(reverse("material_detail", args=[self.lecture.id])).status_code, 200)
        stranger = make_user("stranger", Profile.ROLE_STUDENT, created_by=self.other_teacher)
        self.client.force_login(stranger)
        self.assertEqual(self.client.get(reverse("material_detail", args=[self.lecture.id])).status_code, 404)


# ------------------------------------------------------ teacher workflows

class TeacherFlowTests(TestCase):
    def setUp(self):
        self.subject = Subject.objects.get(slug="physics")
        self.teacher = make_user("teacher", Profile.ROLE_TEACHER)
        self.students = [make_user(f"s{i}", Profile.ROLE_STUDENT, created_by=self.teacher) for i in range(3)]
        self.client.force_login(self.teacher)

    def test_lecture_to_test_to_assign_all(self):
        response = self.client.post(reverse("teacher_lectures"), {
            "subject": self.subject.id, "title": "Newton", "text": "F = m a. Inertia...",
        })
        lecture = Lecture.objects.get(title="Newton")
        self.assertRedirects(response, reverse("teacher_lecture_test", args=[lecture.id]))

        fake = [FILL, CHOICE]
        with mock.patch("core.views_teacher.generate_questions", return_value=fake) as gen:
            response = self.client.post(reverse("teacher_lecture_test", args=[lecture.id]), {
                "interaction_types": [FILL_BLANK, MULTI_SELECT], "count": 5, "title": "",
            })
        self.assertEqual(gen.call_args.kwargs["source_text"], lecture.text)
        teacher_test = TeacherTest.objects.get(teacher=self.teacher)
        self.assertEqual(teacher_test.source, TeacherTest.SOURCE_AI_LECTURE)
        self.assertEqual(teacher_test.title, "Newton")
        self.assertEqual(teacher_test.questions.count(), 2)
        self.assertRedirects(response, reverse("teacher_test_assign", args=[teacher_test.id]))

        self.assertContains(self.client.get(reverse("teacher_test_assign", args=[teacher_test.id])), 'id="select-all"')
        self.client.post(reverse("teacher_test_assign", args=[teacher_test.id]),
                         {"students": [s.id for s in self.students]})
        self.assertEqual(Assignment.objects.filter(teacher_test=teacher_test).count(), 3)
        self.assertEqual(Question.objects.filter(session__teacher_test=teacher_test).count(), 6)

    def test_generation_failure_shows_message(self):
        lecture = Lecture.objects.create(teacher=self.teacher, subject=self.subject, title="L", text="x")
        with mock.patch("core.views_teacher.generate_questions", side_effect=GenerationError("down")):
            response = self.client.post(reverse("teacher_lecture_test", args=[lecture.id]), {
                "interaction_types": [FILL_BLANK, MULTI_SELECT], "count": 5,
            })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(TeacherTest.objects.exists())

    def test_topic_test_requires_subject_and_topic(self):
        with mock.patch("core.views_teacher.generate_questions") as gen:
            response = self.client.post(reverse("teacher_topic_test"), {"interaction_types": [FILL_BLANK, MULTI_SELECT]})
        self.assertEqual(response.status_code, 200)
        gen.assert_not_called()

    def test_upload_template_docx(self):
        from io import BytesIO

        import docx
        from django.core.files.uploadedfile import SimpleUploadedFile

        document = docx.Document()
        for line in ["Q: Match.", "Type: matching", "a = 1", "b = 2"]:
            document.add_paragraph(line)
        buffer = BytesIO()
        document.save(buffer)
        upload = SimpleUploadedFile("t.docx", buffer.getvalue())
        response = self.client.post(reverse("teacher_upload_test"), {
            "subject": self.subject.id, "title": "Match test", "mode": "template", "file": upload,
        })
        teacher_test = TeacherTest.objects.get(title="Match test")
        self.assertRedirects(response, reverse("teacher_test_assign", args=[teacher_test.id]))
        self.assertEqual(TeacherQuestion.objects.get(teacher_test=teacher_test).type, MATCHING)

    def test_manual_lesson_plan(self):
        response = self.client.post(reverse("teacher_lesson_plan_new"), {
            "topic": "Energy", "competences": ["g.1", "d.1", "bogus"], "use_ai": "0", "method": "ll",
            "assessments": ["observation"], "duration": "45 min",
        })
        lesson = LessonPlan.objects.get(topic="Energy")
        self.assertRedirects(response, reverse("teacher_lesson_plan", args=[lesson.id]))
        self.assertEqual(lesson.setting["competences"], ["g.1", "d.1"])
        self.assertFalse(lesson.ai_generated)
        page = self.client.get(reverse("teacher_lesson_plan", args=[lesson.id]))
        self.assertContains(page, "Laboratory learning")
        self.assertContains(page, "Observation")

    def test_ai_lesson_plan_and_fallback(self):
        plan = validate_plan({"teaching_method": {"code": "pbl", "why": "Real problem"},
                              "timeline": [{"minutes": 10, "activity": "Intro"}], "final_assessment": []})
        with mock.patch("core.views_teacher.design_lesson", return_value=plan) as design:
            self.client.post(reverse("teacher_lesson_plan_new"), {"topic": "Water", "competences": ["g.3"], "use_ai": "1"})
        self.assertEqual(design.call_args.args[1], ["Promoting nature"])
        self.assertTrue(LessonPlan.objects.get(topic="Water").ai_generated)

        with mock.patch("core.views_teacher.design_lesson", side_effect=GenerationError("down")):
            self.client.post(reverse("teacher_lesson_plan_new"),
                             {"topic": "Air", "competences": ["g.3"], "use_ai": "1", "method": "sl"})
            response = self.client.post(reverse("teacher_lesson_plan_new"),
                                        {"topic": "Fire", "competences": ["g.3"], "use_ai": "1"})
        self.assertFalse(LessonPlan.objects.get(topic="Air").ai_generated)  # fell back to the chosen card
        self.assertFalse(LessonPlan.objects.filter(topic="Fire").exists())  # nothing to fall back to
        self.assertEqual(response.status_code, 200)


class PlanValidationTests(TestCase):
    def test_unknown_codes_are_dropped(self):
        self.assertIsNone(validate_plan({"teaching_method": {"code": "magic"}}))
        plan = validate_plan({
            "teaching_method": {"code": "cl"},
            "diagnostic_assessment": {"code": "nope", "how": "x"},
            "final_assessment": {"code": "observation", "how": "watch"},
            "principles": ["reflection", "made_up"],
            "timeline": [{"minutes": "ten", "activity": "Talk"}, {"activity": ""}],
        })
        self.assertIsNone(plan["diagnostic_assessment"])
        self.assertEqual(plan["final_assessment"], [{"code": "observation", "how": "watch"}])
        self.assertEqual(plan["principles"], ["reflection"])
        self.assertEqual(plan["timeline"], [{"minutes": 0, "activity": "Talk"}])


# ----------------------------------------------------------- pages & i18n

class PageSmokeTests(TestCase):
    """Every page renders in every language (catches template typos and missing strings)."""

    def setUp(self):
        self.subject = Subject.objects.get(slug="math")
        self.teacher = make_user("teacher", Profile.ROLE_TEACHER)
        self.student = make_user("student", Profile.ROLE_STUDENT, created_by=self.teacher)
        self.lecture = Lecture.objects.create(teacher=self.teacher, subject=self.subject, title="Lecture", text="a\nb")
        plan = validate_plan({"teaching_method": {"code": "vcp", "why": "w"}, "steps": ["s"], "output": "o",
                              "diagnostic_assessment": {"code": "questions", "how": "h"},
                              "final_assessment": [{"code": "authentic", "how": "h"}], "resources": ["r"],
                              "timeline": [{"minutes": 5, "activity": "a"}], "principles": ["community"],
                              "learning_outcomes": ["lo"], "quiz_topic": "q"})
        self.plan = LessonPlan.objects.create(teacher=self.teacher, subject=self.subject, topic="Plan", plan=plan,
                                              setting={"competences": ["e.1"], "transversal": ["teamwork"], "aim": "x"})
        self.teacher_test = TeacherTest.objects.create(teacher=self.teacher, subject=self.subject, title="TT",
                                                       source=TeacherTest.SOURCE_TEMPLATE_PARSED)
        self.done = make_session(self.student, self.subject, status=TestSession.STATUS_COMPLETED, total_questions=2)
        for q in self.done.questions.all():
            Answer.objects.create(question=q, submitted_data={}, is_correct=False)
        self.ready = make_session(self.student, self.subject)

    def pages(self, role):
        common = ["/", reverse("guide"), reverse("offline"), reverse("leaderboard"), reverse("history"),
                  reverse("quiz_setup")]
        if role == "teacher":
            return common + [
                reverse("teacher_dashboard"), reverse("teacher_upload_test"), reverse("teacher_topic_test"),
                reverse("teacher_lectures"), reverse("teacher_lecture_test", args=[self.lecture.id]),
                reverse("teacher_lesson_plans"), reverse("teacher_lesson_plan_new"),
                reverse("teacher_lesson_plan", args=[self.plan.id]),
                reverse("teacher_lesson_plan_test", args=[self.plan.id]),
                reverse("teacher_test_assign", args=[self.teacher_test.id]),
                reverse("teacher_test_results", args=[self.teacher_test.id]),
                reverse("material_detail", args=[self.lecture.id]),
            ]
        return common + [
            reverse("assigned_tests"), reverse("materials"), reverse("material_detail", args=[self.lecture.id]),
            reverse("quiz_take", args=[self.ready.id]), reverse("quiz_results", args=[self.done.id]),
            reverse("quiz_review", args=[self.done.id]),
        ]

    def test_all_pages_all_languages(self):
        for user, role in [(self.teacher, "teacher"), (self.student, "student")]:
            self.client.force_login(user)
            for lang in LANGUAGE_CODES:
                session = self.client.session
                session["language"] = lang
                session.save()
                for url in self.pages(role):
                    with self.subTest(role=role, lang=lang, url=url):
                        self.assertEqual(self.client.get(url).status_code, 200)

    def test_pwa_files(self):
        sw = self.client.get("/sw.js")
        self.assertEqual(sw["Content-Type"], "application/javascript")
        self.assertIn("networkFirst", sw.content.decode())
        manifest = json.loads(self.client.get("/manifest.webmanifest").content)
        self.assertEqual(manifest["short_name"], "TeachX")

    def test_every_language_defines_every_key(self):
        english = set(TRANSLATIONS["en"])
        for lang in LANGUAGE_CODES:
            with self.subTest(lang=lang):
                self.assertEqual(english - set(TRANSLATIONS[lang]), set())
        self.assertEqual(get_strings("xx")["nav_guide"], TRANSLATIONS["en"]["nav_guide"])


class ScaffoldContentTests(TestCase):
    def test_counts_match_the_deck(self):
        self.assertEqual(len(scaffold.COMPETENCES), 57)  # 21 + 15 + 9 + 12
        self.assertEqual(len(scaffold.TEACHING_METHODS), 7)
        self.assertEqual(len(scaffold.ASSESSMENT_METHODS), 7)
        self.assertEqual(len(scaffold.TRANSVERSAL), 7)
        self.assertEqual(len(scaffold.PRINCIPLES), 7)

    def test_every_language_is_complete(self):
        for lang in ("en", "ru", "uz", "kaa"):
            content = scaffold.localized(lang)
            for method in content["methods"]:
                self.assertTrue(method["title"] and method["description"] and len(method["steps"]) == 5)
            for principle in content["principles"]:
                self.assertIn(principle["try_method"], scaffold.METHODS_BY_CODE)
