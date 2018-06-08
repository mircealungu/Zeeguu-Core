import newspaper

import zeeguu
from tests_zeeguu.model_test_mixin import ModelTestMixIn
from tests_zeeguu.rules.language_rule import LanguageRule
from tests_zeeguu.rules.rss_feed_rule import RSSFeedRule
from tests_zeeguu.rules.user_rule import UserRule
from zeeguu.content_retriever.content_cleaner import cleanup_non_content_bits
from zeeguu.content_retriever.article_downloader import download_from_feed
from zeeguu.content_retriever.quality_filter import sufficient_quality
from zeeguu.model import Topic, LocalizedTopic, ArticleWord


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
        topic = Topic("Spiegel")
        zeeguu.db.session.add(topic)
        zeeguu.db.session.commit()
        loc_topic = LocalizedTopic(topic, self.lan, "spiegelDE", "spiegel")
        zeeguu.db.session.add(loc_topic)
        zeeguu.db.session.commit()

        download_from_feed(feed, zeeguu.db.session, 3)

        article = feed.get_articles(self.user, limit=2)[0]

        assert (topic in article.topics)

    def testDownloadWithWords(self):
        feed = RSSFeedRule().feed1

        download_from_feed(feed, zeeguu.db.session, 3)

        article = feed.get_articles(self.user, limit=2)[0]

        word = article.title.split()[2]
        articleword = ArticleWord.find_by_word(word)

        assert (article in articleword.articles)

    def testSufficientQuality(self):
        u = "https://www.propublica.org/article/" \
            "warren-buffett-recommends-investing-in-index-funds-but-many-of-his-employees-do-not-have-that-option"

        art = newspaper.Article(u)
        art.download()
        art.parse()

        assert (sufficient_quality(art, {}))

    def testNewScientistOverlay(self):
        u = "https://www.newscientist.com/" \
            "article/2164774-in-30-years-asian-pacific-fish-will-be-gone-and-then-were-next/"

        art = newspaper.Article(u)
        art.download()
        art.parse()

        assert (not sufficient_quality(art, {}))

    def testLeMondeEditionAbonee(self):
        u = "http://www.lemonde.fr/ameriques/article/" \
            "2018/03/24/quand-les-vols-americains-se-transforment-en-arche-de-noe_5275773_3222.html"

        art = newspaper.Article(u)
        art.download()
        art.parse()

        assert (not sufficient_quality(art, {}))

    def testFragmentRemoval(self):
        url = 'https://www.theonion.com/u-s-military-announces-plan-to-consolidate-all-wars-in-1824018300'
        art = newspaper.Article(url)
        art.download()
        art.parse()

        cleaned_up_text = cleanup_non_content_bits(art.text)
        assert ("Advertisement" not in cleaned_up_text)
