import zeeguu
from tests_core_zeeguu.model_test_mixin import ModelTestMixIn
from tests_core_zeeguu.rules.language_rule import LanguageRule
from tests_core_zeeguu.rules.rss_feed_rule import RSSFeedRule
from tests_core_zeeguu.rules.user_rule import UserRule
from zeeguu.content_retriever.article_downloader import download_from_feed


class TestRetrieveAndCompute(ModelTestMixIn):
    def setUp(self):
        super().setUp()

        self.user = UserRule().user
        self.lan = LanguageRule().de

    def testDifficultyOfFeedItems(self):
        feed = RSSFeedRule().spiegel
        download_from_feed(feed, zeeguu.db.session, 3)

        articles = feed.get_articles(self.user, limit=2)

        assert len(articles) == 2
        assert articles[0].fk_difficulty
