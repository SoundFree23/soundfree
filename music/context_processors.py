from .translations import TRANSLATIONS


def language_context(request):
    lang = request.session.get('lang', 'ro')
    if lang not in TRANSLATIONS:
        lang = 'ro'
    return {
        't': TRANSLATIONS[lang],
        'current_lang': lang,
    }


def radio_context(request):
    """Expune slot-ul curent de radio ca variabilă globală în template-uri."""
    from .radio import get_current_slot, get_slot_display
    lang = request.session.get('lang', 'ro')
    slot_id, slot = get_current_slot()
    return {
        'radio_slot_id': slot_id,
        'radio_slot_emoji': slot['emoji'],
        'radio_slot_name': get_slot_display(slot, lang),
    }


def install_prompt_context(request):
    """Pop the post-login flag so the install modal fires exactly once after login."""
    if not hasattr(request, 'session'):
        return {'offer_install_prompt': False}
    show = bool(request.session.pop('offer_install_prompt', False))
    return {'offer_install_prompt': show}
