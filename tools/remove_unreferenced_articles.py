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
import sqlalchemy
import traceback

from zeeguu_core.model import Article, UserArticle, UserActivityData, UserReadingSession
from zeeguu_core import db

import sys

dbs = db.session

BATCH_COMMIT_SIZE = 5000


def is_the_article_referenced(article, print_reference_info):
    info = UserArticle.find_by_article(article)
    interaction_data = UserActivityData.query.filter_by(article_id=article.id).all()
    reading_session_info = UserReadingSession.query.filter_by(article_id=article.id).all()

    referenced = info or interaction_data or reading_session_info

    if print_reference_info and referenced:
        print(f"WON'T DELETE ID:{article.id} -- {article.title}")

        for ainfo in info:
            print(ainfo.user_info_as_string())

        if interaction_data:
            print("interaction data: " + str(interaction_data[0]))

        if reading_session_info:
            print("reading session info: " + str(reading_session_info[0]))

    return referenced


def delete_articles_older_than(days):
    print(f"Finding articles older than {DAYS} days...")
    all_articles = Article.all_older_than(days=DAYS)
    print(f" ... article count: {len(all_articles)}")

    i = 0
    referenced_in_this_batch = 0
    deleted = []
    for each in all_articles:
        i += 1
        print(f"#{i} -- ID: {each.id}")

        if is_the_article_referenced(each, True):
            referenced_in_this_batch += 1
            continue

        try:
            deleted.append(each.id)
            dbs.delete(each)

            if i % BATCH_COMMIT_SIZE == 0:
                print(f"Keeping {referenced_in_this_batch} articles from the last {BATCH_COMMIT_SIZE} batch...")
                dbs.commit()
                print("The rest are now deleted!!!")
                referenced_in_this_batch = 0

        except sqlalchemy.exc.IntegrityError as e:
            traceback.print_exc()
            dbs.rollback()
            continue

    print(f'Deleted: {deleted}')


if __name__ == "__main__":

    try:
        DAYS = int(sys.argv[1])
    except:
        print("\nOOOPS: you must provide a number of days before which the articles to be deleted\n")
        exit(-1)

    delete_articles_older_than(DAYS)
