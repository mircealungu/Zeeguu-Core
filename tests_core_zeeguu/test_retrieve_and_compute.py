from tests_core_zeeguu.model_test_mixin import ModelTestMixIn
from tests_core_zeeguu.rules.language_rule import LanguageRule
from tests_core_zeeguu.rules.user_rule import UserRule
from tests_core_zeeguu.testing_data import *
from zeeguu.language.retrieve_and_compute import \
    retrieve_urls_and_compute_metrics
from zeeguu.model.feed import RSSFeed
from zeeguu.model.url import Url


class TestRetrieveAndCompute(ModelTestMixIn):
    def setUp(self):
        super().setUp()

        self.user = UserRule().user
        self.lan = LanguageRule().de

    def testSimple(self):
        urls = [EASIEST_STORY_URL,
                VERY_EASY_STORY_URL,
                EASY_STORY_URL]

        difficulties = retrieve_urls_and_compute_metrics(urls, self.lan, self.user)

        difficulty_for_easiest = difficulties[EASIEST_STORY_URL]['difficulty']
        difficulty_for_easy = difficulties[EASY_STORY_URL]['difficulty']

        assert difficulty_for_easiest['average'] < difficulty_for_easy['average']

        # on the other hand, they're all EASY
        # assert difficulty_for_easiest['discrete'] == difficulty_for_very_easy['discrete']

    def testDifficultyOfFeedItems(self):
        url = Url(DE_SAMPLE_FEED_1_URL, DE_SAMPLE_FEED_1_URL)
        feed = RSSFeed(url, DE_SAMPLE_FEED_1_TITLE, "blabla", image_url=None,
                       language=self.lan)

        items_with_metrics = feed.feed_items_with_metrics(self.user, 20)

        assert len(items_with_metrics) > 0
        assert items_with_metrics[0]["title"]
        assert items_with_metrics[0]["summary"]
        assert items_with_metrics[0]["published"]
        assert items_with_metrics[0]["metrics"]
