from unittest import TestCase

from tests_core_zeeguu.model_test_mixin import ModelTestMixIn

import zeeguu
from tests_core_zeeguu.rules.article_rule import ArticleRule

session = zeeguu.db.session


class ArticleTest(ModelTestMixIn, TestCase):

    def setUp(self):
        super().setUp()
        self.article1 = ArticleRule().article
        self.article2 = ArticleRule().article

    def test_articles_are_different(self):
        assert (self.article1.title != self.article2.title)

    def test_article_representation_does_not_error(self):
        assert self.article1.article_info()