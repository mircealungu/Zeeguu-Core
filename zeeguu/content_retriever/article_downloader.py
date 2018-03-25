"""

    Goes through all the interesting sources that the server knows
    about and downloads new articles saving them in the DB.  


"""
from datetime import datetime

import newspaper

import zeeguu

from zeeguu import model
from zeeguu.content_retriever.content_cleaner import cleanup_non_content_bits
from zeeguu.content_retriever.quality_filter import sufficient_quality
from zeeguu.model import Url, RSSFeed, Topic
from zeeguu.constants import SIMPLE_TIME_FORMAT

LOG_CONTEXT = "FEED RETRIEVAL"


def download_from_feed(feed: RSSFeed, session, limit=1000):
    """

        Session is needed because this saves stuff to the DB.


        last_crawled_time is useful because otherwise there would be a lot of time
        wasted trying to retrieve the same articles, especially the ones which
        can't be retrieved, so they won't be cached.


    """
    zeeguu.log(feed)
    downloaded = 0
    skipped = 0
    skipped_due_to_low_quality = dict()
    skipped_already_in_db = 0

    last_retrieval_time_from_DB = None
    last_retrieval_time_seen_this_crawl = None

    if feed.last_crawled_time:
        last_retrieval_time_from_DB = feed.last_crawled_time
        zeeguu.log(f"last retrieval time from DB = {last_retrieval_time_from_DB}")

    for feed_item in feed.feed_items():

        if downloaded >= limit:
            break

        url = feed_item['url']

        # solve redirects and save the clean url
        import requests
        response = requests.get(url)
        url = response.url

        # drop all the query params from the urls and keep the canonical url
        from urllib.parse import urlparse
        o = urlparse(url)
        url = o.scheme + "://" + o.netloc + o.path

        try:
            this_article_time = datetime.strptime(feed_item['published'], SIMPLE_TIME_FORMAT)
            this_article_time = this_article_time.replace(tzinfo=None)
        except:
            zeeguu.log(f"can't get time from {url}: {feed_item['published']}")
            continue

        if last_retrieval_time_from_DB:

            if this_article_time < last_retrieval_time_from_DB:
                skipped += 1
                continue

        title = feed_item['title']
        summary = feed_item['summary']

        art = model.Article.find(url)

        if (not last_retrieval_time_seen_this_crawl) or (this_article_time > last_retrieval_time_seen_this_crawl):
            last_retrieval_time_seen_this_crawl = this_article_time

        if art:
            skipped_already_in_db += 1
        else:
            try:

                art = newspaper.Article(url)
                art.download()
                art.parse()

                cleaned_up_text = cleanup_non_content_bits(art.text)

                quality_article = sufficient_quality(art, skipped_due_to_low_quality)
                if quality_article:
                    from zeeguu.language.difficulty_estimator_factory import DifficultyEstimatorFactory

                    # Create new article and save it to DB
                    new_article = zeeguu.model.Article(
                        Url.find_or_create(session, url),
                        title,
                        ', '.join(art.authors),
                        cleaned_up_text,
                        summary,
                        this_article_time,
                        feed,
                        feed.language
                    )
                    session.add(new_article)
                    session.commit()
                    downloaded += 1

                    for each in Topic.query.all():
                        if each.language == new_article.language and each.matches_article(new_article):
                            new_article.add_topic(each)
            except Exception as e:
                # raise e
                import sys
                ex = sys.exc_info()[0]
                zeeguu.log(f" {LOG_CONTEXT}: Failed to create zeeguu.Article from {url}\n{str(ex)}")

    zeeguu.log(f'  Skipped due to time: {skipped} ')
    zeeguu.log(f'  Downloaded: {downloaded}')
    zeeguu.log(f'  Low Quality: {skipped_due_to_low_quality}')
    zeeguu.log(f'  Already in DB: {skipped_already_in_db}')

    if last_retrieval_time_seen_this_crawl:
        feed.last_crawled_time = last_retrieval_time_seen_this_crawl
    session.add(feed)
    session.commit()
