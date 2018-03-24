import newspaper

import zeeguu
from tests_zeeguu.model_test_mixin import ModelTestMixIn
from tests_zeeguu.rules.language_rule import LanguageRule
from tests_zeeguu.rules.rss_feed_rule import RSSFeedRule
from tests_zeeguu.rules.user_rule import UserRule
from zeeguu.content_retriever.article_downloader import download_from_feed
from zeeguu.content_retriever.article_quality_filter import sufficient_quality
from zeeguu.model import Topic


class TestRetrieveAndCompute(ModelTestMixIn):
    def setUp(self):
        super().setUp()

        self.user = UserRule().user
        self.lan = LanguageRule().de

    def testDifficultyOfFeedItems(self):
        feed = RSSFeedRule().feed1
        download_from_feed(feed, zeeguu.db.session, 3)

        articles = feed.get_articles(self.user, limit=2)

        assert len(articles) == 2
        assert articles[0].fk_difficulty

    def testDownloadWithTopic(self):
        feed = RSSFeedRule().feed1
        topic = Topic("#spiegel", feed.language, "www.spiegel")
        zeeguu.db.session.add(topic)
        zeeguu.db.session.commit()

        download_from_feed(feed, zeeguu.db.session, 3)

        article = feed.get_articles(self.user, limit=2)[0]

        assert (topic in article.topics)
        # print (topic.all_articles())

    def testSufficientQuality(self):

        quality_urls = [
            "https://www.propublica.org/article/warren-buffett-recommends-investing-in-index-funds-but-many-of-his-employees-do-not-have-that-option"
        ]

        non_quality_urls = [
            "https://www.newscientist.com/article/2164774-in-30-years-asian-pacific-fish-will-be-gone-and-then-were-next/",
            "https://edition.cnn.com/2018/03/14/us/students-who-did-not-walkout-trnd/index.html",
            "http://www.lemonde.fr/ameriques/article/2018/03/24/quand-les-vols-americains-se-transforment-en-arche-de-noe_5275773_3222.html"
        ]

        for each in quality_urls:
            art = newspaper.Article(each)
            art.download()
            art.parse()

            assert (sufficient_quality(art, {}))

        for each in non_quality_urls:
            art = newspaper.Article(each)
            art.download()
            art.parse()

            assert (not sufficient_quality(art, {}))

