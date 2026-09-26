from django.conf import settings
from django.db import models

from core.question_types import ALL_TYPES

DIFFICULTY_EASY = "easy"
DIFFICULTY_NORMAL = "normal"
DIFFICULTY_HARD = "hard"
DIFFICULTY_EXPERT = "expert"
DIFFICULTY_CHOICES = [
    (DIFFICULTY_EASY, "Easy"),
    (DIFFICULTY_NORMAL, "Normal"),
    (DIFFICULTY_HARD, "Hard"),
    (DIFFICULTY_EXPERT, "Expert"),
]
DIFFICULTY_CODES = [code for code, _ in DIFFICULTY_CHOICES]


class Profile(models.Model):
    ROLE_ADMIN = "admin"
    ROLE_TEACHER = "teacher"
    ROLE_STUDENT = "student"
    ROLE_CHOICES = [
        (ROLE_ADMIN, "Admin"),
        (ROLE_TEACHER, "Teacher"),
        (ROLE_STUDENT, "Student"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_STUDENT)
    # Who created this account — lets a teacher's roster be "students I created",
    # with no separate class/roster table needed.
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_accounts"
    )

    def __str__(self):
        return f"{self.user} ({self.role})"


class Subject(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=60, unique=True)
    icon = models.CharField(max_length=8, default="📘")
    color = models.CharField(max_length=7, default="#6366f1")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class TeacherTest(models.Model):
    SOURCE_AI_PARSED = "ai_parsed"
    SOURCE_TEMPLATE_PARSED = "template_parsed"
    SOURCE_CHOICES = [
        (SOURCE_AI_PARSED, "AI-parsed"),
        (SOURCE_TEMPLATE_PARSED, "Template-parsed"),
    ]

    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="authored_tests")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="teacher_tests")
    title = models.CharField(max_length=120)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, null=True, blank=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    language = models.CharField(max_length=8, default="en")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.subject})"


class TeacherQuestion(models.Model):
    teacher_test = models.ForeignKey(TeacherTest, on_delete=models.CASCADE, related_name="questions")
    order = models.PositiveSmallIntegerField()
    type = models.CharField(max_length=20)
    prompt = models.TextField()
    data = models.JSONField(default=dict)
    explanation = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(fields=["teacher_test", "order"], name="unique_teacher_question_order"),
        ]

    def __str__(self):
        return f"Q{self.order} ({self.type}) · {self.teacher_test_id}"


class TestSession(models.Model):
    STATUS_GENERATING = "generating"
    STATUS_READY = "ready"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_ABANDONED = "abandoned"
    STATUS_CHOICES = [
        (STATUS_GENERATING, "Generating"),
        (STATUS_READY, "Ready"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
        (STATUS_ABANDONED, "Abandoned"),
    ]

    SOURCE_AI = "ai"
    SOURCE_TEACHER = "teacher"
    SOURCE_CHOICES = [
        (SOURCE_AI, "Self-service AI"),
        (SOURCE_TEACHER, "Teacher-assigned"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sessions")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="sessions")
    requested_count = models.PositiveSmallIntegerField()
    interaction_types = models.JSONField(default=list)
    language = models.CharField(max_length=8, default="en")
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_GENERATING)
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default=SOURCE_AI)
    teacher_test = models.ForeignKey(
        TeacherTest, on_delete=models.SET_NULL, null=True, blank=True, related_name="sessions"
    )
    score = models.PositiveSmallIntegerField(default=0)
    total_questions = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} · {self.subject} · {self.requested_count}q"

    @property
    def percentage(self):
        if not self.total_questions:
            return 0
        return round(100 * self.score / self.total_questions)

    def valid_interaction_types(self):
        return [t for t in self.interaction_types if t in ALL_TYPES]


class Assignment(models.Model):
    teacher_test = models.ForeignKey(TeacherTest, on_delete=models.CASCADE, related_name="assignments")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assignments")
    test_session = models.OneToOneField(TestSession, on_delete=models.CASCADE, related_name="assignment")
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-assigned_at"]

    def __str__(self):
        return f"{self.teacher_test} → {self.student}"


class Question(models.Model):
    session = models.ForeignKey(TestSession, on_delete=models.CASCADE, related_name="questions")
    order = models.PositiveSmallIntegerField()
    type = models.CharField(max_length=20)
    prompt = models.TextField()
    data = models.JSONField(default=dict)
    explanation = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(fields=["session", "order"], name="unique_question_order_per_session"),
        ]

    def __str__(self):
        return f"Q{self.order} ({self.type}) · session {self.session_id}"


class Answer(models.Model):
    question = models.OneToOneField(Question, on_delete=models.CASCADE, related_name="answer")
    submitted_data = models.JSONField(default=dict)
    is_correct = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Answer to {self.question_id} ({'correct' if self.is_correct else 'incorrect'})"
