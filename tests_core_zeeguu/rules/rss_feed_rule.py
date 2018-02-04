from datetime import datetime, timedelta
from random import randint

from tests_core_zeeguu.rules.base_rule import BaseRule
from tests_core_zeeguu.rules.language_rule import LanguageRule
from tests_core_zeeguu.rules.url_rule import UrlRule
from zeeguu.model import RSSFeed, Language, Url


class RSSFeedRule(BaseRule):
    """

        Creates a RSSFeed object with random data and saves it to the database

    """

    def __init__(self):
        super().__init__()

        self.rss_feed = self._create_model_object()
        self.feed = self.rss_feed

        self.save(self.rss_feed)

    def _create_model_object(self):
        title = " ".join(self.faker.text().split()[:(randint(1, 10))])
        description = " ".join(self.faker.text().split()[:(randint(5, 20))])
        language = LanguageRule().random
        url = UrlRule().url
        image_url = UrlRule().url

        new_rss_feed = RSSFeed(url, title, description, image_url, language)

        if RSSFeed.exists(new_rss_feed):
            return self._create_model_object()

        return new_rss_feed

    @classmethod
    def der_spiegel_feed(self):
        TEST_FEED_URL = "http://www.spiegel.de/index.rss"
        TEST_FEED_LANG = "de"

        url = Url.find_or_create(self.db.session, TEST_FEED_URL)
        feed = RSSFeed(url, "", "", image_url=None,
                       language=Language.find_or_create(TEST_FEED_LANG))
        return feed
