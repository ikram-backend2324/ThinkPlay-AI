from django.contrib import admin
from django.urls import include, path

from core import views

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', views.landing, name='landing'),
    path('set-language/', views.set_language_view, name='set_language'),

    path('accounts/login/', views.login_view, name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('accounts/post-login/', views.post_login_redirect, name='post_login_redirect'),
    path('accounts/history/', views.history, name='history'),

    path('quiz/setup/', views.quiz_setup, name='quiz_setup'),
    path('quiz/<int:session_id>/generating/', views.quiz_generating, name='quiz_generating'),
    path('quiz/<int:session_id>/generate-batch/', views.generate_batch, name='generate_batch'),
    path('quiz/<int:session_id>/take/', views.quiz_take, name='quiz_take'),
    path('quiz/<int:session_id>/submit/', views.quiz_submit, name='quiz_submit'),
    path('quiz/<int:session_id>/abandon/', views.quiz_abandon, name='quiz_abandon'),
    path('quiz/<int:session_id>/results/', views.quiz_results, name='quiz_results'),
    path('quiz/<int:session_id>/review/', views.quiz_review, name='quiz_review'),

    path('assigned/', views.assigned_tests, name='assigned_tests'),

    path('teacher/', include('core.urls_teacher')),
]
