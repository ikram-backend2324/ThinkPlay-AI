from django.conf import settings
from django.db import models

from core.question_types import ALL_TYPES


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


class TestSession(models.Model):
    STATUS_GENERATING = "generating"
    STATUS_READY = "ready"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_GENERATING, "Generating"),
        (STATUS_READY, "Ready"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sessions")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="sessions")
    requested_count = models.PositiveSmallIntegerField()
    interaction_types = models.JSONField(default=list)
    language = models.CharField(max_length=8, default="en")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_GENERATING)
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
