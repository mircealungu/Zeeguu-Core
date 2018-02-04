from datetime import datetime

import watchmen
import zeeguu

from zeeguu import model
from zeeguu.model import Url, RSSFeed

LOG_CONTEXT = "FEED RETRIEVAL"


def download_from_feed(feed: RSSFeed, session, limit=1000):
    """

        Session is needed because this saves stuff to the DB.


    """
    for feed_item in feed.feed_items()[:limit]:

        title = feed_item['title']
        url = feed_item['url']

        art = model.Article.find(url)

        if art:
            print(f"Already in the DB: {art}")
        else:
            try:
                art = watchmen.article_parser.get_article(url)

                word_count = len(art.text.split(" "))

                if word_count < 10:
                    zeeguu.log_n_print(f" {LOG_CONTEXT}: Can't find text for: {url}")

                else:
                    from zeeguu.language.difficulty_estimator_factory import DifficultyEstimatorFactory

                    # Create new article and save it to DB
                    new_article = zeeguu.model.Article(
                        Url.find_or_create(session, url),
                        title,
                        ', '.join(art.authors),
                        art.text,
                        datetime.now(),
                        feed,
                        feed.language
                    )
                    session.add(new_article)
                    session.commit()
                    zeeguu.log_n_print(f" {LOG_CONTEXT}: Added: {new_article}")
            except Exception as ex:
                zeeguu.log_n_print(f" {LOG_CONTEXT}: Failed to create zeeguu.Article from {url}\n{str(ex)}")
                raise (ex)
