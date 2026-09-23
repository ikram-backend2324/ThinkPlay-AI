from django import template

from core.i18n import subject_name as _subject_name

register = template.Library()


@register.filter
def localized_subject(subject, lang):
    return _subject_name(subject, lang)
