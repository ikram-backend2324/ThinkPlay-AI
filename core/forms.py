from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class CreateAccountForm(UserCreationForm):
    """Used by a teacher to create a student login, and by admin's Jazzmin
    User-add form. Closed system — there is no public-facing registration."""

    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
