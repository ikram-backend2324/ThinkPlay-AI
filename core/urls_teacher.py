from django.urls import path

from core import views_teacher as views

urlpatterns = [
    path('', views.teacher_dashboard, name='teacher_dashboard'),
    path('students/add/', views.add_student, name='teacher_add_student'),
    path('students/<int:user_id>/remove/', views.remove_student, name='teacher_remove_student'),
    path('tests/upload/', views.upload_test, name='teacher_upload_test'),
    path('tests/from-topic/', views.topic_test, name='teacher_topic_test'),
    path('tests/<int:test_id>/assign/', views.assign_test, name='teacher_test_assign'),
    path('tests/<int:test_id>/results/', views.test_results, name='teacher_test_results'),
    path('lectures/', views.lectures, name='teacher_lectures'),
    path('lectures/<int:lecture_id>/test/', views.lecture_test, name='teacher_lecture_test'),
    path('lectures/<int:lecture_id>/delete/', views.delete_lecture, name='teacher_lecture_delete'),
    path('lessons/', views.lesson_plans, name='teacher_lesson_plans'),
    path('lessons/new/', views.lesson_plan_new, name='teacher_lesson_plan_new'),
    path('lessons/<int:plan_id>/', views.lesson_plan_detail, name='teacher_lesson_plan'),
    path('lessons/<int:plan_id>/delete/', views.lesson_plan_delete, name='teacher_lesson_plan_delete'),
    path('lessons/<int:plan_id>/test/', views.lesson_plan_test, name='teacher_lesson_plan_test'),
]
