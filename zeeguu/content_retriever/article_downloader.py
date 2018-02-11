from datetime import datetime

import watchmen
import zeeguu

from zeeguu import model
from zeeguu.model import Url, RSSFeed, Article

LOG_CONTEXT = "FEED RETRIEVAL"


def download_from_feed(feed: RSSFeed, session, limit=1000):
    """

        Session is needed because this saves stuff to the DB.


    """
    downloaded = 0
    for feed_item in feed.feed_items():

        if downloaded >= limit:
            break

        title = feed_item['title']
        url = feed_item['url']
        summary = feed_item['summary']

        art = model.Article.find(url)

        if art:
            print(f"Already in the DB: {art}")
        else:
            try:
                art = watchmen.article_parser.get_article(url)

                word_count = len(art.text.split(" "))

                if word_count < 10:
                    zeeguu.log_n_print(f" {LOG_CONTEXT}: Can't find text for: {url}")
                elif word_count < Article.MINIMUM_WORD_COUNT:
                    zeeguu.log_n_print(f" {LOG_CONTEXT}: Skipped. Less than {Article.MINIMUM_WORD_COUNT} words of text. {url}")
                else:
                    from zeeguu.language.difficulty_estimator_factory import DifficultyEstimatorFactory

                    # Create new article and save it to DB
                    new_article = zeeguu.model.Article(
                        Url.find_or_create(session, url),
                        title,
                        ', '.join(art.authors),
                        art.text,
                        summary,
                        datetime.now(),
                        feed,
                        feed.language
                    )
                    session.add(new_article)
                    session.commit()
                    zeeguu.log_n_print(f" {LOG_CONTEXT}: Added: {new_article}")
                    downloaded += 1
            except:
                import sys
                ex = sys.exc_info()[0]
                zeeguu.log_n_print(f" {LOG_CONTEXT}: Failed to create zeeguu.Article from {url}\n{str(ex)}")
