import sqlalchemy
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound
from datetime import time

from zeeguu.model import User

import zeeguu

db = zeeguu.db


class UserLanguage(db.Model):
    __table_args__ = {'mysql_collate': 'utf8_bin'}

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey(User.id))
    user = relationship(User)

    from zeeguu.model.language import Language

    language_id = Column(db.Integer, ForeignKey(Language.id))
    language = relationship(Language)

    user_main_learned_language = User.learned_language

    def __init__(self, user, language):
        self.user = user
        self.language = language

    def get(self):
        return self.value

    def __str__(self):
        return f'User language (uid: {self.user_id}, language:"{self.Language}")'

    # Specific Getter / Setter Methods below
    # --------------------------------------

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
    def get_all_user_languages(cls, user: User):
        user_main_learned_language = user.learned_language
        user_languages = [language_id.language for language_id in cls.query.filter(cls.user == user).all()]

        if user_main_learned_language not in user_languages:
            user_languages.append(user_main_learned_language)

        return user_languages
