from .translations import TRANSLATIONS


def language_context(request):
    lang = request.session.get('lang', 'ro')
    if lang not in TRANSLATIONS:
        lang = 'ro'
    return {
        't': TRANSLATIONS[lang],
        'current_lang': lang,
    }
