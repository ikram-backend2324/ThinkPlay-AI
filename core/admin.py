from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from core.models import (
    Answer, Assignment, Profile, Question, Subject, TeacherQuestion, TeacherTest, TestSession,
)


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    fk_name = "user"

    def get_extra(self, request, obj=None, **kwargs):
        # A brand-new user (obj is None on the add page, or an older account
        # with no Profile yet) needs one blank row to actually set a role —
        # with extra=0 the formset would render zero visible fields there,
        # letting an account get created with no role at all.
        return 0 if obj and hasattr(obj, "profile") else 1

    def get_max_num(self, request, obj=None, **kwargs):
        return 1


class CustomUserAdmin(UserAdmin):
    inlines = [ProfileInline]
    list_display = UserAdmin.list_display + ("get_role",)

    @admin.display(description="Role")
    def get_role(self, obj):
        return getattr(obj, "profile", None) and obj.profile.get_role_display()


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


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
    list_display = ("id", "user", "subject", "source", "status", "score", "total_questions", "created_at")
    list_filter = ("status", "source", "subject", "difficulty")
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


class TeacherQuestionInline(admin.TabularInline):
    model = TeacherQuestion
    extra = 0
    fields = ("order", "type", "prompt")


@admin.register(TeacherTest)
class TeacherTestAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "teacher", "subject", "source", "difficulty", "created_at")
    list_filter = ("source", "subject", "difficulty")
    search_fields = ("title", "teacher__username")
    inlines = [TeacherQuestionInline]


@admin.register(TeacherQuestion)
class TeacherQuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "teacher_test", "order", "type")
    list_filter = ("type",)


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("id", "teacher_test", "student", "assigned_at")
    search_fields = ("student__username",)
