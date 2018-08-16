import zeeguu

from sqlalchemy import Column, Integer, String

db = zeeguu.db


class Topic(db.Model):
    """

        A topic is the general (English) name of a topic,
        the localized_topic contains the language, translation,
        and the keywords used to find the articles.

    """
    __table_args__ = {'mysql_collate': 'utf8_bin'}

    id = Column(Integer, primary_key=True)

    title = Column(String(64))

    def __init__(self, title):
        self.title = title

    def __repr__(self):
        return f'<Topic {self.title}>'

    def as_dictionary(self):

        return dict(
            id=self.id,
            title=self.title,
        )

    def all_articles(self):
        from zeeguu.model import Article

        if hasattr(Topic, 'cached_articles') and (self.cached_articles.get(self.id, None)):
            return Topic.cached_articles[self.id]

        if not hasattr(Topic, 'cached_articles'):
            Topic.cached_articles = {}

        print("computing and caching the articles for topic: "+ self.title)
        Topic.cached_articles[self.id] = Article.query.filter(Article.topics.any(id=self.id)).all()

        return Topic.cached_articles[self.id]

    def clear_all_articles_cache(self):
        Topic.cached_articles[self.id] = None

    @classmethod
    def find(cls, name: str):
        try:
            return cls.query.filter(cls.title == name).one()
        except Exception as e:
            print(e)
            return None

    @classmethod
    def find_by_id(cls, i):
        try:
            result = cls.query.filter(cls.id == i).one()
            return result
        except Exception as e:
            print(e)
            return None

    @classmethod
    def get_all_topics(cls):
        return Topic.query.all()
