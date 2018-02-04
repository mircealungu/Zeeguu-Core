import datetime
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound

import zeeguu

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UnicodeText

from zeeguu.language.difficulty_estimator_factory import DifficultyEstimatorFactory

db = zeeguu.db


class Article(db.Model):
    __table_args__ = {'mysql_collate': 'utf8_bin'}

    id = Column(Integer, primary_key=True)

    title = Column(String(512))
    authors = Column(UnicodeText)
    content = Column(UnicodeText())
    summary = Column(UnicodeText)
    word_count = Column(Integer)
    published_time = Column(DateTime)
    fk_difficulty = Column(Integer)

    from zeeguu.model.url import Url

    from zeeguu.model.feed import RSSFeed

    from zeeguu.model.language import Language

    rss_feed_id = Column(Integer, ForeignKey(RSSFeed.id))
    rss_feed = relationship(RSSFeed)

    url_id = Column(Integer, ForeignKey(Url.id), unique=True)
    url = relationship(Url)

    language_id = Column(Integer, ForeignKey(Language.id))
    language = relationship(Language)

    def __init__(self, url, title, authors, content, summary, published_time, rss_feed, language):
        self.url = url
        self.title = title
        self.authors = authors
        self.content = content
        self.summary = summary
        self.published_time = published_time
        self.rss_feed = rss_feed
        self.language = language

        fk_estimator = DifficultyEstimatorFactory.get_difficulty_estimator("fk")
        fk_difficulty = fk_estimator.estimate_difficulty(self.content, self.language, None)['normalized']

        # easier to store integer in the DB
        # otherwise we have to use Decimal, and it's not supported on all dbs
        self.fk_difficulty = int(fk_difficulty * 100)
        self.word_count = len(self.content.split())

    def __repr__(self):
        return f'<Article {self.title} (w: {self.word_count}, d: {self.fk_difficulty}) ({self.url})>'

    def article_info_NEW_VERSION(self):
        """

            This is the data that is sent over the API
            to the Reader. Whatever the reader needs
            must be here.

        :return:
        """
        return dict(
            id=self.id,
            title=self.title,
            url=self.url.as_string(),
            published=self.published_time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            summary=self.summary,
            metrics=dict(
                difficulty_fk=self.fk_difficulty,
                word_count=self.word_count
            )
        )

    def article_info(self):
        """

            This is the data that is sent over the API
            to the Reader. Whatever the reader needs
            must be here.

        :return:
        """
        return dict(
            id=self.id,
            title=self.title,
            url=self.url.as_string(),
            published=self.published_time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            summary=self.summary,
            metrics=dict(
                difficulty=dict(
                    discrete="HARD",
                    normalized=str(self.fk_difficulty / 100)
                ),
                word_count=self.word_count
            )
        )

    @classmethod
    def find(cls, url: str):
        """

            Find by url

        :return: object or None if not found
        """

        from zeeguu.model import Url
        try:
            url_object = Url.find(url)
            return (cls.query.filter(cls.url == url_object)).one()
        except:
            return None

    @classmethod
    def exists(cls, article):
        try:
            cls.query.filter(
                cls.url == article.url
            ).one()
            return True
        except NoResultFound:
            return False
