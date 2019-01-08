from datetime import datetime, timedelta
from random import randint

from test.rules.article_rule import ArticleRule
from test.rules.base_rule import BaseRule
from test.rules.language_rule import LanguageRule
from test.rules.rss_feed_rule import RSSFeedRule
from test.rules.url_rule import UrlRule
from test.rules.user_rule import UserRule
from zeeguu.model import Article
from zeeguu.model.user_article import UserArticle


class UserArticleRule(BaseRule):
    """

        Creates a User Article object with random data and saves it to the database.

    """

    def __init__(self):
        super().__init__()

        self.user_article = self._create_model_object()

        self.save(self.user_article)

    def _create_model_object(self):
        user = UserRule().user
        article = ArticleRule().article

        user_article = UserArticle(user, article)

        if self._exists_in_db(user_article):
            return self._create_model_object()

        return user_article

    @staticmethod
    def _exists_in_db(obj):
        return UserArticle.exists(obj)
