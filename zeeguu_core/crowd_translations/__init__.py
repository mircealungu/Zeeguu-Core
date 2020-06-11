from sqlalchemy.orm.exc import NoResultFound

from zeeguu_core.model import User, Language, UserWord, Text, Bookmark


def own_or_crowdsourced_translation(user, word: str, from_lang_code: str, context: str):

    own_past_translation = get_own_past_translation(user, word, from_lang_code, context)

    if own_past_translation:
        translations = [{'translation': own_past_translation,
                         'service_name': 'Own Last Translation',
                         'quality': 100}]
        return translations

    others_past_translation = get_others_past_translation(word, from_lang_code, context)
    if others_past_translation:
        translations = [{'translation': others_past_translation,
                         'service_name': 'Contributed Translation',
                         'quality': 100}]
        return translations

    return None


def get_others_past_translation(word: str, from_lang_code: str, context: str):
    return _get_past_translation(word, from_lang_code, context)


def get_own_past_translation(user, word: str, from_lang_code: str, context: str):
    return _get_past_translation(word, from_lang_code, context, user)


def _get_past_translation(word: str, from_lang_code: str, context: str, user: User = None):
    try:

        from_language = Language.find(from_lang_code)

        origin_word = UserWord.find(word, from_language)

        text = Text.query.filter_by(content=context).one()

        query = Bookmark.query.filter_by(origin_id=origin_word.id, text_id=text.id)

        if user:
            query = query.filter_by(user_id=user.id)

        # prioritize older users
        query.order_by(Bookmark.user_id.asc())

        return query.first().translation.word

    except Exception as e:
        print(e)
        return None
