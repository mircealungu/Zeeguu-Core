# -*- coding: utf8 -*-

import time

import feedparser
import sqlalchemy.orm.exc
import zeeguu

from zeeguu.model.language import Language
from zeeguu.model.url import Url

db = zeeguu.db


class RSSFeed(db.Model):
    __table_args__ = {'mysql_collate': 'utf8_bin'}
    __tablename__ = 'rss_feed'

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(2083))
    description = db.Column(db.String(2083))

    language_id = db.Column(db.Integer, db.ForeignKey(Language.id))
    language = db.relationship(Language)

    url_id = db.Column(db.Integer, db.ForeignKey(Url.id))
    url = db.relationship(Url, foreign_keys=url_id)

    image_url_id = db.Column(db.Integer, db.ForeignKey(Url.id))
    image_url = db.relationship(Url, foreign_keys=image_url_id)

    def __init__(self, url, title, description, image_url=None, language=None):
        self.url = url
        self.image_url = image_url
        self.title = title
        self.language = language
        self.description = description

    def as_dictionary(self):
        image_url = ""
        if self.image_url:
            image_url = self.image_url.as_string()

        return dict(
            id=self.id,
            title=self.title,
            url=self.url.as_string(),
            description=self.description,
            language=self.language.code,
            image_url=image_url
        )

    def feed_items(self):
        feed_data = feedparser.parse(self.url.as_string())
        feed_items = [
            dict(
                title=item.get("title", ""),
                url=item.get("link", ""),
                content=item.get("content", ""),
                summary=item.get("summary", ""),
                published=time.strftime("%Y-%m-%dT%H:%M:%S%z", item.published_parsed)
            )
            for item in feed_data.entries]

        return feed_items

    @classmethod
    def find_by_id(cls, i):
        try:
            result = cls.query.filter(cls.id == i).one()
            return result
        except Exception as e:
            print(e)
            return None


    @classmethod
    def find_by_url(cls, url):
        try:
            result = cls.query.filter(cls.url == url).one()
            return result
        except sqlalchemy.orm.exc.NoResultFound:
            return None

    def feed_items_with_metrics(self, user, timeout=10):
        """
        Retrieves the feed items for this feed together with their metrics (difficulty,
        learnability, etc.).

        Assumes that the language of the feed is correctly set

        :return: dictionary with keys being urls and values being the corresponding metrics
        """
        from zeeguu.language.retrieve_and_compute import retrieve_urls_and_compute_metrics

        feed_items = self.feed_items()
        urls = [each['url'] for each in feed_items]
        urls_and_metrics = retrieve_urls_and_compute_metrics(urls,
                                                             self.language,
                                                             user,
                                                             timeout)
        filtered_feed_items = [dict(list(each.items()) + list({"metrics":urls_and_metrics.get(each['url'])}.items()))
                               for each in feed_items
                               if each["url"] in list(urls_and_metrics.keys())]

        return filtered_feed_items

    @classmethod
    def find_or_create(cls, session, url, title, description, image_url: Url, language: Language):

        try:
            result = (cls.query.filter(cls.url == url)
                      .filter(cls.title == title)
                      .filter(cls.language == language)
                      .filter(cls.description == description)
                      .one())
            return result
        except sqlalchemy.orm.exc.NoResultFound:
            new = cls(url, title, description, image_url, language)
            session.add(new)
            session.commit()
            return new

    # although it seems to not be used by anybody,
    # this method is being used from the zeeguu-api
    # project.
    # @classmethod
    def find_for_language_id(cls, language_code):
        return cls.query.filter(cls.language.code == language_code).group_by(cls.title).all()
