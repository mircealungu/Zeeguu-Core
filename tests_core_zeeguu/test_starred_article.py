import json

import zeeguu
from tests_core_zeeguu.model_test_mixin import ModelTestMixIn
from tests_core_zeeguu.rules.language_rule import LanguageRule
from tests_core_zeeguu.rules.url_rule import UrlRule
from tests_core_zeeguu.rules.user_rule import UserRule
from zeeguu.model.starred_article import StarredArticle


class StarredArticleTest(ModelTestMixIn):
    def setUp(self):
        super().setUp()

        self.user_rule = UserRule()
        self.user = self.user_rule.user

        self.url_rule = UrlRule()
        self.url = self.url_rule.url

        self.url_rule2 = UrlRule()
        self.url2 = self.url_rule2.url

        self.language_rule = LanguageRule()
        self.language = self.language_rule.en

    def test_new_starring_two_articles(self):
        # GIVEN:
        StarredArticle.find_or_create(zeeguu.db.session, self.user, self.url.as_string(),  self.url.title,
                                      self.language.code)
        # WHEN:
        StarredArticle.find_or_create(zeeguu.db.session, self.user, self.url2.as_string(),  self.url2.title,
                                      self.language.code)
        # THEN:
        self.assertEqual(2, len(StarredArticle.all_for_user(self.user)))

    def test_delete_starred_article(self):
        # GIVEN:
        StarredArticle.find_or_create(zeeguu.db.session, self.user, self.url.as_string(),  self.url.title,
                                      self.language.code)
        # WHEN:
        StarredArticle.delete(zeeguu.db.session, self.user, self.url.as_string())

        # THEN:
        self.assertEqual(0, len(StarredArticle.all_for_user(self.user)))

    def test_converts_to_dict(self):
        # GIVEN:
        x = StarredArticle.find_or_create(zeeguu.db.session, self.user, self.url.as_string(), self.url.title,
                                          self.language.code)
        # WHEN:
        jsonified = json.dumps(x.as_dict())

        # THEN
        self.assertTrue(self.url.title in jsonified)
