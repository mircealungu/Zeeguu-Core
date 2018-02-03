from sqlalchemy.orm import relationship

import zeeguu

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, DECIMAL, UnicodeText

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

    def __init__(self, url, title, authors, content, fk_difficulty, word_count, published_time, rss_feed, language):
        self.url = url
        self.title = title
        self.authors = authors
        self.content = content
        self.fk_difficulty = fk_difficulty
        self.word_count = word_count
        self.published_time = published_time
        self.rss_feed = rss_feed
        self.language = language

    def __repr__(self):
        return f'<Article {self.title} (w: {self.word_count}, d: {self.fk_difficulty}) ({self.url})>'

    @classmethod
    def find(cls, url: str):

        from zeeguu.model import Url
        try:
            url_object = Url.find(url)
            return (cls.query.filter(cls.url == url_object)).one()
        except:
            return None
