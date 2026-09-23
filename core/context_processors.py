from core.i18n import DEFAULT_LANGUAGE, LANGUAGES, get_strings


def language(request):
    lang = getattr(request, "session", {}).get("language", DEFAULT_LANGUAGE)
    return {
        "t": get_strings(lang),
        "LANG": lang,
        "LANGUAGES": LANGUAGES,
    }
