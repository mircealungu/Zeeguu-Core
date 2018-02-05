import zeeguu
from tests_core_zeeguu.model_test_mixin import ModelTestMixIn
from tests_core_zeeguu.rules.language_rule import LanguageRule
from tests_core_zeeguu.rules.rss_feed_rule import RSSFeedRule
from tests_core_zeeguu.rules.user_rule import UserRule
from tests_core_zeeguu.testing_data import *
from zeeguu.content_retriever.article_downloader import download_from_feed
from zeeguu.language.retrieve_and_compute import \
    retrieve_urls_and_compute_metrics


class TestRetrieveAndCompute(ModelTestMixIn):
    def setUp(self):
        super().setUp()

        self.user = UserRule().user
        self.lan = LanguageRule().de

    def testSimple(self):
        urls = [EASIEST_STORY_URL,
                VERY_EASY_STORY_URL,
                EASY_STORY_URL]

        urls_and_metrics = retrieve_urls_and_compute_metrics(urls, self.lan, self.user)

        difficulty_for_easiest = urls_and_metrics[EASIEST_STORY_URL]['difficulty']
        difficulty_for_easy = urls_and_metrics[EASY_STORY_URL]['difficulty']

        assert difficulty_for_easiest['normalized'] < difficulty_for_easy['normalized']

        word_count = urls_and_metrics[EASY_STORY_URL]['word_count']
        assert word_count > 1400


        # on the other hand, they're all EASY
        # assert difficulty_for_easiest['discrete'] == difficulty_for_very_easy['discrete']

    def testDifficultyOfFeedItems(self):
        feed = RSSFeedRule().spiegel
        download_from_feed(feed, zeeguu.db.session, 3)

        items_with_metrics = feed.feed_items_with_metrics(self.user, 2)

        assert len(items_with_metrics) == 2

        assert items_with_metrics[0]["title"]
        assert items_with_metrics[0]["summary"]
        assert items_with_metrics[0]["published"]
        assert items_with_metrics[0]["metrics"]
