# Script:
#
# remove all articles from the DB which have no
# references to them and are older than a number of days
#
# works with the db that is defined in the configuration
# pointed by ZEEGUU_CORE_CONFIG
#
# takes as argument the number of days before which the
# articles will be deleted.
#
# call like this to remove all articles older than 90 days
#
#
#      python remove_unreferenced_articles.py 90
#
#
#


from zeeguu_core.model import Article, UserArticle, UserActivityData
from zeeguu_core import db

dbs = db.session

import sys

try:
    DAYS = int(sys.argv[1])
except:
    print ("\nOOOPS: you must provide a number of days before which the articles to be deleted\n")
    exit(-1)

deleted = []

print("1. finding urls in activity data...")
all_urls = set()
all_activity_data = UserActivityData.query.all()
for each in all_activity_data:
    url = each.find_url_in_extra_data()
    if url:
        all_urls.add(url)
print(f" ... url count: {len(all_urls)}")

#

print(f"2. finding articles older than {DAYS} days...")
all_articles = Article.all_older_than(days=DAYS)
print(f" ... article count: {len(all_articles)}")

i = 0
for each in all_articles:
    i += 1
    info = UserArticle.find_by_article(each)
    url_found = each.url.as_string() in all_urls

    if info or url_found:
        if info:
            print(f"WON'T DELETE info! {each.id} {each.title}")
            for ainfo in info:
                print(ainfo.user_info_as_string())
        if url_found:
            print(f"WON'T DELETE url_found! {each.id} {each.title}")
    else:
        deleted.append(each.id)
        dbs.delete(each)

    if i == 1000:
        dbs.commit()
        i = 0

dbs.commit()

print(f'Deleted: {deleted}')
