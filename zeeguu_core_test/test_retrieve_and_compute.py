import newspaper

import zeeguu_core
from zeeguu_core_test.model_test_mixin import ModelTestMixIn
from zeeguu_core_test.rules.language_rule import LanguageRule
from zeeguu_core_test.rules.rss_feed_rule import RSSFeedRule
from zeeguu_core_test.rules.user_rule import UserRule
from zeeguu_core.content_retriever.content_cleaner import cleanup_non_content_bits
from zeeguu_core.content_retriever.article_downloader import download_from_feed, strip_article_title_word
from zeeguu_core.content_retriever.quality_filter import sufficient_quality
from zeeguu_core.model import Topic, LocalizedTopic, ArticleWord


class TestRetrieveAndCompute(ModelTestMixIn):
    def setUp(self):
        super().setUp()

        self.user = UserRule().user
        self.lan = LanguageRule().de

    def testDifficultyOfFeedItems(self):
        feed = RSSFeedRule().feed1
        download_from_feed(feed, zeeguu_core.db.session, 3)

        articles = feed.get_articles(limit=2)

        assert len(articles) == 2
        assert articles[0].fk_difficulty

    def testDownloadWithTopic(self):
        feed = RSSFeedRule().feed1
        topic = Topic("Spiegel")
        zeeguu_core.db.session.add(topic)
        zeeguu_core.db.session.commit()
        loc_topic = LocalizedTopic(topic, self.lan, "spiegelDE", "spiegel")
        zeeguu_core.db.session.add(loc_topic)
        zeeguu_core.db.session.commit()

        download_from_feed(feed, zeeguu_core.db.session, 3)

        article = feed.get_articles(limit=2)[0]

        assert (topic in article.topics)

    def testDownloadWithWords(self):
        feed = RSSFeedRule().feed1

        download_from_feed(feed, zeeguu_core.db.session, 3)

        article = feed.get_articles(limit=2)[0]

        # Try two words, as one might be filtered out
        word = strip_article_title_word(article.title.split()[0])
        article_word = ArticleWord.find_by_word(word)

        if word in ['www', ''] or word.isdigit() or len(word) < 3 or len(word) > 25:
            assert (article_word is None)
        else:
            assert (article in article_word.articles)

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
