from django.contrib import admin

from core.models import Answer, Question, Subject, TestSession


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "icon", "color", "order")
    ordering = ("order", "name")


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    fields = ("order", "type", "prompt")
    readonly_fields = ("order", "type", "prompt")
    can_delete = False


@admin.register(TestSession)
class TestSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "subject", "status", "score", "total_questions", "created_at")
    list_filter = ("status", "subject")
    search_fields = ("user__username",)
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "order", "type")
    list_filter = ("type",)


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("id", "question", "is_correct", "answered_at")
    list_filter = ("is_correct",)
