"""

    Goes through all the interesting sources that the server knows
    about and downloads new articles saving them in the DB.  


"""
from datetime import datetime

import newspaper
import re

import zeeguu

from zeeguu import model
from zeeguu.content_retriever.content_cleaner import cleanup_non_content_bits
from zeeguu.content_retriever.quality_filter import sufficient_quality
from zeeguu.model import Url, RSSFeed, LocalizedTopic, ArticleWord
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

                    add_topics(new_article, session)
                    add_searches(title, url, new_article, session)

                    try:
                        session.commit()
                    except Exception as e:
                        zeeguu.log(f'{LOG_CONTEXT}: Something went wrong when committing words/topic to article: {e}')

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


def add_topics(new_article, session):
    for loc_topic in LocalizedTopic.query.all():
        if loc_topic.language == new_article.language and loc_topic.matches_article(new_article):
            new_article.add_topic(loc_topic.topic)
            session.add(new_article)


def add_searches(title, url, new_article, session):

    """
    This method takes the relevant keywords from the title
    and URL, and tries to properly clean them.
    It finally adds the ArticleWord to the session, to be committed as a whole.
    :param title: The title of the article
    :param url: The url of the article
    :param new_article: The actual new article
    :param session: The session to which it should be added.
    """

    # Split the title, path and url netloc (sub domain)
    all_words = title.split()
    from urllib.parse import urlparse
    # Parse the URL so we can call netloc and path without a lot of regex
    parsed_url = urlparse(url)
    all_words.append(re.split('; |, |\*|-|%20|/', parsed_url.path))
    all_words.append(parsed_url.netloc.split('.')[0])
    for word in all_words:
        # Strip the unwanted characters
        word.strip('":;?!<>\'').lower()
        # Check if the word is of proper length, not only digits and not empty or www
        if word in ['www', '', ' '] or word.isdigit() or len(word) < 3 or len(word) > 25:
            continue
        else:
            # Find or create the ArticleWord and add it to the session
            article_word_obj = ArticleWord.find_by_word(word)
            if article_word_obj is None:
                article_word_obj = ArticleWord(word)
            article_word_obj.add_article(new_article)
            session.add(article_word_obj)