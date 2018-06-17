#!/usr/bin/env python

"""

   Script that goes through all the feeds that are
   available in the DB and retrieves the newest articles
   in order to populate the DB with them.

   The DB is populated by saving Article objects in the
   articles table.

   Before this script checking whether there were new items
   in a given feed was done while serving the request for
   items to read. That was too slow.

   To be called from a cron job.

"""

import zeeguu
from zeeguu.model import Article, Language, LocalizedTopic

session = zeeguu.db.session

counter = 0

languages = Language.available_languages()

for language in languages:
    articles = Article.query.filter(Article.language == language).all()
    loc_topics = LocalizedTopic.all_for_language(language)

    for article in articles:
        counter += 1
        for loc_topic in loc_topics:
            if loc_topic.matches_article(article):
                article.add_topic(loc_topic.topic)
                print(f" #{loc_topic.topic_translated}: {article.url.as_string()}")
        session.add(article)
        if counter == 1000:
            print("1k more done. comitting... ")
            session.commit()
            counter = 0
