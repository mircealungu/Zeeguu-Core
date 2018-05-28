from sqlalchemy.orm.exc import NoResultFound
from datetime import datetime

import zeeguu

db = zeeguu.db


class Language(db.Model):
    __table_args__ = {'mysql_collate': 'utf8_bin'}
    __tablename__ = 'language'

    LANGUAGES_THAT_CAN_BE_LEARNED = ['de', 'es', 'fr', 'nl', 'en', 'it']
    LANGUAGES_AVAILABLE_AS_NATIVE = ['en', 'nl', 'zh-CN']

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(5))
    name = db.Column(db.String(255), unique=True)

    languages = {
        "de": "German",
        "en": "English",
        "es": "Spanish",
        "fr": "French",
        "nl": "Dutch",
        "it": "Italian",
        "zh-CN": "Chinese"
    }

    def __init__(self, code, name):
        self.code = code
        self.name = name

    def __repr__(self):
        return '<Language %r>' % self.code

    def __eq__(self, other):
        return self.code == other.code or self.name == other.name

    def as_dictionary(self):

        return dict(
            id=self.id,
            code=self.code,
            language=self.name,

        )

    @classmethod
    def default_learned(cls):
        return cls.find_or_create("de")

    @classmethod
    def default_native_language(cls):
        return cls.find_or_create("en")

    @classmethod
    def native_languages(cls):
        return [Language.find_or_create(code) for code in cls.LANGUAGES_AVAILABLE_AS_NATIVE]

    @classmethod
    def available_languages(cls):
        return [Language.find_or_create(code) for code in cls.LANGUAGES_THAT_CAN_BE_LEARNED]

    @classmethod
    def find(cls, code):
        result = cls.query.filter(Language.code == code).one()
        return result

    @classmethod
    def find_or_create(cls, language_id):
        try:
            language = cls.find(language_id)

        except NoResultFound:
            language = cls(language_id, cls.languages[language_id])
            db.session.add(language)
            db.session.commit()

        return language

    @classmethod
    def all(cls):
        return cls.query.filter().all()

    @classmethod
    def find_by_id(cls, i):
        return cls.query.filter(Language.id == i).one()

    def get_articles(self, limit=None, after_date=None, most_recent_first=False, easiest_first=False):
        """

            Articles for this language from the article DB

        :param limit:
        :param after_date:
        :param most_recent_first:
        :param easiest_first:
        :return:
        """

        from zeeguu.model import Article

        if not after_date:
            after_date = datetime(2001, 1, 1)

        try:
            q = (Article.query.
                 filter(Article.language == self).
                 filter(Article.broken == 0).
                 filter(Article.published_time >= after_date).
                 filter(Article.word_count > Article.MINIMUM_WORD_COUNT))

            if most_recent_first:
                q = q.order_by(Article.published_time.desc())
            if easiest_first:
                q = q.order_by(Article.fk_difficulty)

            return q.limit(limit).all()

        except Exception as e:
            raise (e)
            return None
