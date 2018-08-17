from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.exc import NoResultFound

import zeeguu

from sqlalchemy import Column, Integer, String, ForeignKey, Table

db = zeeguu.db

article_word_map = Table('article_word_map',
                         db.Model.metadata,
                         Column('word_id', Integer,
                                ForeignKey('article_word.id')),
                         Column('article_id', Integer,
                                ForeignKey('article.id'))
                         )


class ArticleWord(db.Model):
    __table_args__ = {'mysql_collate': 'utf8_bin'}

    id = Column(Integer, primary_key=True)

    word = Column(String(30))

    from zeeguu.model.article import Article

    articles = relationship(Article,
                            secondary="article_word_map",
                            backref=backref('words'),
                            uselist=False)

    def __init__(self, word):
        self.word = word

    def __repr__(self):
        return f'<Word {self.word}>'

    def add_article(self, article):
        self.articles.append(article)

    @classmethod
    def find_or_create(cls, session, word):
        try:
            return cls.query.filter(cls.word == word).one()
        except NoResultFound:
            new = cls(word)
            session.add(new)
            session.commit()
            return new

    @classmethod
    def find_by_word(cls, word):
        try:
            return cls.query.filter(cls.word == word).one_or_none()
        except Exception as e:
            print(e)
            return None

    @classmethod
    def get_articles_for_word(cls, word):
        try:
            result = cls.query.filter(cls.word.like(word + "%")).all()

            all_articles = []
            for each in result:
                print(each)
                print(each.articles)
                all_articles.append(each.articles)

            return all_articles

        except Exception as e:
            print(e)
            return None
