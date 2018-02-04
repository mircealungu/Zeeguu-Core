import datetime
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound

import zeeguu

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, DECIMAL, UnicodeText

from zeeguu.language.difficulty_estimator_factory import DifficultyEstimatorFactory

db = zeeguu.db


class Article(db.Model):
    __table_args__ = {'mysql_collate': 'utf8_bin'}

    id = Column(Integer, primary_key=True)

    title = Column(String(512))
    authors = Column(UnicodeText)
    content = Column(UnicodeText())
    word_count = Column(Integer)
    published_time = Column(DateTime)
    fk_difficulty = Column(DECIMAL(4, 2))

    from zeeguu.model.url import Url

    from zeeguu.model.feed import RSSFeed

    from zeeguu.model.language import Language

    rss_feed_id = Column(Integer, ForeignKey(RSSFeed.id))
    rss_feed = relationship(RSSFeed)

    url_id = Column(Integer, ForeignKey(Url.id), unique=True)
    url = relationship(Url)

    language_id = Column(Integer, ForeignKey(Language.id))
    language = relationship(Language)

    def __init__(self, url, title, authors, content, published_time, rss_feed, language):
        self.url = url
        self.title = title
        self.authors = authors
        self.content = content
        self.published_time = published_time
        self.rss_feed = rss_feed
        self.language = language

        fk_estimator = DifficultyEstimatorFactory.get_difficulty_estimator("fk")
        fk_difficulty = fk_estimator.estimate_difficulty(self.content, self.language, None)['normalized']

        self.fk_difficulty = fk_difficulty
        self.word_count = len(self.content.split())

    def __repr__(self):
        return f'<Article {self.title} (w: {self.word_count}, d: {self.fk_difficulty}) ({self.url})>'

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

    @classmethod
    def get_all_for_feed(cls, feed: RSSFeed, limit=None, after_date=None):
        """

            Articles for feed.

        :param feed:
        :param limit:
        :param order_by:
        :return:
        """

        if not after_date:
            after_date = datetime.datetime(2001, 1, 1)

        query = (cls.query.
                 filter(cls.rss_feed == feed).
                 filter(cls.published_time >= after_date).
                 order_by(cls.fk_difficulty).
                 limit(limit))

        try:
            return query.all()
        except:
            return None
