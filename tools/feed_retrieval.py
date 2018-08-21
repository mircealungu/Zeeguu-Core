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
from zeeguu.content_retriever.article_downloader import download_from_feed
from zeeguu.model import RSSFeed

session = zeeguu.db.session

counter = 0
for feed in RSSFeed.query.all():
    counter += 1
    print(f"{counter}: DOWNLOADING {feed.title}".encode('utf-8'))
    download_from_feed(feed, zeeguu.db.session)
    print(f"{counter}: FINISHED DOWNLOADING {feed.title}".encode('utf-8'))

