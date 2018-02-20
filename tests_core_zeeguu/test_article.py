from unittest import TestCase

from tests_core_zeeguu.model_test_mixin import ModelTestMixIn

import zeeguu
from tests_core_zeeguu.rules.article_rule import ArticleRule
from tests_core_zeeguu.rules.language_rule import LanguageRule
from zeeguu.model import Topic

session = zeeguu.db.session


class ArticleTest(ModelTestMixIn, TestCase):

    def setUp(self):
        super().setUp()
        self.article1 = ArticleRule().article
        self.article2 = ArticleRule().article
        self.language = LanguageRule.get_or_create_language("en")

    def test_articles_are_different(self):
        assert (self.article1.title != self.article2.title)

    def test_article_representation_does_not_error(self):
        assert self.article1.article_info()

    def test_add_topic(self):
        health = Topic("health", self.language)
        sports = Topic("sports", self.language)
        self.article1.add_topic(health)
        self.article1.add_topic(sports)
        assert len (self.article1.topics) == 2