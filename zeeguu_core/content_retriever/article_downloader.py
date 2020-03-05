"""

    Goes through all the interesting sources that the server knows
    about and downloads new articles saving them in the DB.  


"""
from datetime import datetime

import newspaper
import re

import zeeguu_core

from zeeguu_core import model
from zeeguu_core.content_retriever.content_cleaner import cleanup_non_content_bits
from zeeguu_core.content_retriever.quality_filter import sufficient_quality
from zeeguu_core.model import Url, RSSFeed, LocalizedTopic, ArticleWord
from zeeguu_core.constants import SIMPLE_TIME_FORMAT
from elasticsearch import Elasticsearch
import requests

LOG_CONTEXT = "FEED RETRIEVAL"


def log(msg: str):
    zeeguu_core.log(LOG_CONTEXT + " " + msg)


def _url_after_redirects(url):
    # solve redirects and save the clean url
    response = requests.get(url)
    return response.url


def _date_in_the_future(time):
    from datetime import datetime
    return time > datetime.now()


def download_from_feed(feed: RSSFeed, session, limit=1000, save_in_elastic=True):
    """

        Session is needed because this saves stuff to the DB.


        last_crawled_time is useful because otherwise there would be a lot of time
        wasted trying to retrieve the same articles, especially the ones which
        can't be retrieved, so they won't be cached.


    """
    log(feed.title)

    downloaded = 0
    skipped = 0
    skipped_due_to_low_quality = dict()
    skipped_already_in_db = 0

    last_retrieval_time_from_DB = None
    last_retrieval_time_seen_this_crawl = None

    if feed.last_crawled_time:
        last_retrieval_time_from_DB = feed.last_crawled_time
        log(f"last retrieval time from DB = {last_retrieval_time_from_DB}")

    try:
        items = feed.feed_items()
    except:
        log("Failed to connect to feed")
        return

    for feed_item in items:

        if downloaded >= limit:
            break

        try:
            url = _url_after_redirects(feed_item['url'])
        except requests.exceptions.TooManyRedirects:
            log(f"Too many redirects for: {url}")
            continue
        except Exception:
            log(f"could not get url after redirects for: {url}")
            continue

        try:
            this_article_time = datetime.strptime(feed_item['published'], SIMPLE_TIME_FORMAT)
            this_article_time = this_article_time.replace(tzinfo=None)
        except:
            log(f"can't get time from {url}: {feed_item['published']}")
            continue

        if _date_in_the_future(this_article_time):
            log("article from the future...")
            continue

        if last_retrieval_time_from_DB:

            if this_article_time < last_retrieval_time_from_DB:
                skipped += 1
                continue

        title = feed_item['title']
        summary = feed_item['summary']

        log(url)

        try:
            art = model.Article.find(url)
        except:
            import sys
            ex = sys.exc_info()[0]
            log(f" {LOG_CONTEXT}: For some reason excepted during Article.find \n{str(ex)}")
            continue

        if (not last_retrieval_time_seen_this_crawl) or (this_article_time > last_retrieval_time_seen_this_crawl):
            last_retrieval_time_seen_this_crawl = this_article_time

        if art:
            skipped_already_in_db += 1
            log("- already in db")
        else:
            try:

                art = newspaper.Article(url)
                art.download()
                art.parse()
                log("- succesfully parsed")

                cleaned_up_text = cleanup_non_content_bits(art.text)

                quality_article = sufficient_quality(art, skipped_due_to_low_quality)
                if quality_article:
                    from zeeguu_core.language.difficulty_estimator_factory import DifficultyEstimatorFactory

                    try:
                        # Create new article and save it to DB
                        #todo replace with elasticsearch
                        new_article = zeeguu_core.model.Article(
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
                        print("saved article in db")
                        downloaded += 1

                        try:
                            add_topics(new_article, session)
                            log("- added topics")
                            add_searches(title, url, new_article, session)
                            log("- added keywords")
                        except Exception as e:
                            print(e)
                        # Saves the news article at ElasticSearch.
                        # We recommend that everything is stored both in SQL and Elasticsearch
                        # as ElasticSearch isn't persistant data
                        if save_in_elastic:
                            es = Elasticsearch(["127.0.0.1:9200"])
                            doc = {
                                'title': new_article.title,
                                'author': new_article.authors,
                                'content': new_article.content,
                                'summary': new_article.summary,
                                'word_count': new_article.word_count,
                                'published_time': new_article.published_time,
                                'topic': " ".join(new_article.topics).strip(),
                                'language': new_article.language.name,
                                'fk_difficulty': new_article.fk_difficulty
                            }
                            res = es.index(index="zeeguu_articles", id=new_article.id, body=doc)
                            print(res['result'])
                        session.commit()

                        if last_retrieval_time_seen_this_crawl:
                            feed.last_crawled_time = last_retrieval_time_seen_this_crawl
                        session.add(feed)

                    except Exception as e:
                        log(f'Something went wrong when creating article and attaching words/topics: {e}')
                        log("rolling back the session... ")
                        session.rollback()

            except Exception as e:
                # raise e
                import sys
                ex = sys.exc_info()[0]
                log(f"Failed to create zeeguu.Article from {url}\n{str(ex)}")

    log(f'  Skipped due to time: {skipped} ')
    log(f'  Downloaded: {downloaded}')
    log(f'  Low Quality: {skipped_due_to_low_quality}')
    log(f'  Already in DB: {skipped_already_in_db}')


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
    all_words += re.split('; |, |\*|-|%20|/', parsed_url.path)
    all_words += parsed_url.netloc.split('.')[0]

    for word in all_words:
        # Strip the unwanted characters
        word = strip_article_title_word(word)
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


def strip_article_title_word(word: str):
    """

        Used when tokenizing the titles of articles
        in order to index them for search

    """
    return word.strip('":;?!<>\'').lower()
