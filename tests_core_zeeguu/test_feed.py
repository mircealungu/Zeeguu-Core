from datetime import datetime, timedelta
from unittest import TestCase

from tests_core_zeeguu.model_test_mixin import ModelTestMixIn

from tests_core_zeeguu.rules.rss_feed_rule import RSSFeedRule
from zeeguu.content_retriever.article_downloader import download_from_feed
from zeeguu.model import Article


class FeedTest(ModelTestMixIn, TestCase):
    def setUp(self):
        super().setUp()

        self.spiegel = RSSFeedRule.der_spiegel_feed()
        download_from_feed(self.spiegel, self.db.session, 3)

    def test_feed_items(self):
        assert len(Article.get_all_for_feed(self.spiegel)) == 3
        assert len(Article.get_all_for_feed(self.spiegel, limit=2)) == 2


    def test_after_date_works(self):
        tomorrow = datetime.now() + timedelta(days=1)
        assert not Article.get_all_for_feed(self.spiegel,after_date=tomorrow)
