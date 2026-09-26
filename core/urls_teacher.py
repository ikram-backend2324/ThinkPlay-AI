from django.urls import path

from core import views_teacher as views

urlpatterns = [
    path('', views.teacher_dashboard, name='teacher_dashboard'),
    path('students/add/', views.add_student, name='teacher_add_student'),
    path('students/<int:user_id>/remove/', views.remove_student, name='teacher_remove_student'),
    path('tests/upload/', views.upload_test, name='teacher_upload_test'),
    path('tests/<int:test_id>/assign/', views.assign_test, name='teacher_test_assign'),
    path('tests/<int:test_id>/results/', views.test_results, name='teacher_test_results'),
]
