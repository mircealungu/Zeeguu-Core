import sqlalchemy
from sqlalchemy import Column, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from zeeguu.model import User

import zeeguu

db = zeeguu.db


class UserLanguage(db.Model):
    """

        A UserLanguage is the 'personalized' version
        of a language. It contains the data about the user
        with respect to the language. Most importantly it
        contains the declared level, inferred level,
        and if the user is reading news / doing exercises.

    """
    __table_args__ = {'mysql_collate': 'utf8_bin'}

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey(User.id))
    user = relationship(User)

    from zeeguu.model.language import Language

    language_id = Column(Integer, ForeignKey(Language.id))
    language = relationship(Language)

    declared_level = Column(Integer)
    inferred_level = Column(Integer)

    reading_news = Column(Boolean)
    doing_exercises = Column(Boolean)

    def __init__(self, user, language, declared_level=0, inferred_level=0, reading_news=False, doing_exercises=False):
        self.user = user
        self.language = language
        self.declared_level = declared_level
        self.inferred_level = inferred_level
        self.reading_news = reading_news
        self.doing_exercises = doing_exercises

    def get(self):
        return self.value

    def __str__(self):
        return f'User language (uid: {self.user_id}, language:"{self.Language}")'

    @classmethod
    def find_or_create(cls, session, user, language):
        try:
            return (cls.query.filter(cls.user == user)
                    .filter(cls.language == language)
                    .one())
        except sqlalchemy.orm.exc.NoResultFound:
            new = cls(user, language)
            session.add(new)
            session.commit()
            return new

    @classmethod
    def with_language_id(cls, i, user):
        return (cls.query.filter(cls.user == user)
                .filter(cls.language_id == i)
                .one())

    @classmethod
    def all_for_user(cls, user):
        user_main_learned_language = user.learned_language
        user_languages = [language_id.language for language_id in cls.query.filter(cls.user == user).all()]

        if user_main_learned_language not in user_languages:
            user_languages.append(user_main_learned_language)

        return user_languages

    @classmethod
    def all_reading_for_user(cls, user):
        result = cls.query.filter(cls.user == user).filter(cls.reading_news == True).all()

        return [language_id.language for language_id in result]
