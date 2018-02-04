from datetime import datetime, timedelta
from random import randint

from tests_core_zeeguu.rules.base_rule import BaseRule
from tests_core_zeeguu.rules.language_rule import LanguageRule
from tests_core_zeeguu.rules.url_rule import UrlRule
from zeeguu.model import RSSFeed, Language, Url

SPIEGEL_URL = "http://www.spiegel.de/index.rss"
TELEGRAAF_URL = "http://www.telegraaf.nl/rss"


class RSSFeedRule(BaseRule):
    """

        Creates a RSSFeed object with random data and saves it to the database

    """

    def __init__(self):
        super().__init__()

        self.rss_feed = self._create_model_object()
        self.feed = self.rss_feed


        german = Language.find_or_create("de")
        url = Url.find_or_create(self.db.session, SPIEGEL_URL)
        self.spiegel = RSSFeed.find_or_create(self.db.session, url, "", "", image_url=None,
                               language=german)

        dutch = Language.find_or_create("de")
        url2 = Url.find_or_create(self.db.session, TELEGRAAF_URL)
        self.telegraaf = RSSFeed.find_or_create(self.db.session,
                                                url2, "", "", image_url=None, language=dutch)

        self.save(self.rss_feed)

    @staticmethod
    def _exists_in_db(obj):
        return RSSFeed.exists(obj)


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
