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
from zeeguu.model import Article, Topic, Language

session = zeeguu.db.session

topics = Topic.query.all()
counter = 0

languages = [Language.find("fr")]

for language in languages:
    articles = Article.query.filter(Article.language == language).all()
    topics = [each for each in topics if each.language == language]

    for article in articles:
        counter += 1
        for topic in topics:
            if topic.matches_article(article):
                article.add_topic(topic)
                print(f" #{topic.name}: {article.url.as_string()}")
        session.add(article)
        if counter == 1000:
            print("1k more done. comitting... ")
            session.commit()
            counter = 0

    for topic in [each for each in topics if each.language == language]:
        print(f'#{topic}: {len(topic.all_articles())}')
