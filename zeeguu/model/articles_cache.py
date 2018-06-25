from sqlalchemy.orm import relationship

import zeeguu

from sqlalchemy import Column, Integer, String, ForeignKey

db = zeeguu.db


class ArticlesCache(db.Model):
    """

        The ArticlesCache is used to increase the speed of retrieving articles
        for certain content filtering configurations. The calculate_hash method
        calculates a hash, consisting of ids of the content selection, and this is
        stored with the articles that belong to this. This way the correct articles
        can be retrieved with a dramatic increase of speed.

    """
    __table_args__ = {'mysql_collate': 'utf8_bin'}

    id = Column(Integer, primary_key=True)

    from zeeguu.model.article import Article

    article_id = Column(Integer, ForeignKey(Article.id))
    article = relationship(Article)

    content_hash = Column(String(256))

    def __init__(self, article, hash):
        self.article = article
        self.content_hash = hash

    def __repr__(self):
        return f'<Hash {self.content_hash}>'

    @staticmethod
    def calculate_hash(topics, filters, searches, search_filters, languages=None, sources=None):
        """

         This method is to calculate the hash with all the content filters.
         It simply adds a letter for the type of content and the sorted ids
         of all the content that has been added.
        :return:

        """
        id_list = []
        if sources is None:
            base_string = "l"
            for lan in languages:
                id_list.append(str(lan.id))
            id_list.sort()
            base_string += ''.join(id_list) + "t"
            id_list = []
        else:
            base_string = "s"
            for source in sources:
                id_list.append(str(source.id))
            id_list.sort()
            base_string += ''.join(id_list) + "t"
            id_list = []
        for topic in topics:
            id_list.append(str(topic.id))
        id_list.sort()
        base_string += ''.join(id_list) + "f"
        id_list = []
        for filter in filters:
            id_list.append(str(filter.id))
        id_list.sort()
        base_string += ''.join(id_list) + "s"
        for search in searches:
            id_list.append(str(search.id))
        id_list.sort()
        base_string += ''.join(id_list) + "sf"
        for search_filter in search_filters:
            id_list.append(str(search_filter.id))
        id_list.sort()
        base_string += ''.join(id_list)
        return base_string

    @classmethod
    def get_articles_for_hash(cls, hash, limit):
        try:
            result = cls.query.filter(cls.content_hash == hash).limit(limit)
            if result is None:
                return None
            return [article_id.article for article_id in result]
        except Exception as e:
            print(e)
            return None

    @classmethod
    def check_if_hash_exists(cls, hash):
        result = cls.query.filter(cls.content_hash == hash).first()
        if result is None:
            return False
        else:
            return True
