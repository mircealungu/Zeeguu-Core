import os

from elasticsearch import Elasticsearch
import sqlalchemy as database
from sqlalchemy.orm import sessionmaker, relationship, backref
from zeeguu_core.model import full_query
from zeeguu_core.content_recommender.mysqlFullText import build_mysql_query
from timeit import default_timer as timer
from zeeguu_core.model import Language
import csv

es = Elasticsearch(["127.0.0.1:9200"])


def query_performance(mysql, difficulty, index, size_of_index, size, content, topics,
                      unwanted_topics, user_topics, unwanted_user_topics):
    language = Language("en", "English")
    language.id = 5
    query_body = full_query(size, content, topics, unwanted_topics,
                            user_topics, unwanted_user_topics, language, 100, 0)

    mysql_query = build_mysql_query(mysql, size, content, topics, unwanted_topics,
                                    user_topics, unwanted_user_topics, language, 100, 0)

    elastic_time_lst = []
    elastic_returned_articles = []
    for i in range(10):
        start = timer()
        res = es.search(index=index, body=query_body)
        elastic_returned_articles.append(len(res['hits'].get('hits')))
        end = timer()
        elastic_time_lst.append(end - start)

    write_results_to_csv(difficulty, size_of_index + " elastic", average_time(elastic_time_lst), size,
                         average(elastic_returned_articles))

    mysql_time_lst = []
    mysql_returned_articles = []
    for i in range(10):
        start = timer()
        result = mysql_query.all()
        mysql_returned_articles.append(len(result))
        end = timer()
        mysql_time_lst.append(end-start)

    write_results_to_csv(difficulty, size_of_index + " MySQL", average_time(mysql_time_lst),
                         size, average(mysql_returned_articles))


def average_time(lst):
    return (sum(lst) / len(lst))*1000


def average(lst):
    return sum(lst) / len(lst)


def write_results_to_csv(difficulty, index, time, asked_for, returned_articles):
    file_exists = os.path.isfile(title_of_csv)
    with open(title_of_csv, 'a', newline='') as csvfile:
        fieldnames = ['Difficulty', 'Index', "Time in MS", "Asked for articles", "Returned articles"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()

        writer.writerow({'Difficulty': difficulty, 'Index': index,
                         'Time in MS': time, 'Asked for articles': asked_for, 'Returned articles': returned_articles})


#---------------------------------------------------------------------------------------------------------------------
def difficulty_5(sessions, requested_articles):
    for session in sessions:
        for nb_articles in requested_articles:
            query_performance(session[0], 5, session[2], session[1], nb_articles, content_difficulty_5, wanted_topics,
                              unwanted_topics, wanted_user_topics, unwanted_user_topics)

    print('Done with difficulty 5')


# ------------------------------------------------------------------------------------------------------------------
def difficulty_4(sessions, requested_articles):
    for session in sessions:
        for nb_articles in requested_articles:
            query_performance(session[0], 4, session[2], session[1], nb_articles, content_difficulty_4,
                              wanted_topics, unwanted_topics, wanted_user_topics, unwanted_user_topics)
    print('Done with difficulty 4')


def difficulty_3(sessions, requested_articles):
    for session in sessions:
        for nb_articles in requested_articles:
            query_performance(session[0], 3, session[2], session[1], nb_articles, content_difficulty_3, wanted_topics,
                              unwanted_topics, wanted_user_topics, unwanted_user_topics)

    print('Done with difficulty 3')


# -----------------------------------------------------------------------------------------------------------------
# Difficulty 2
def difficulty_2(sessions, requested_articles):
    for session in sessions:
        for nb_articles in requested_articles:
            query_performance(session[0], 2, session[2], session[1], nb_articles, '', wanted_topics,
                              unwanted_topics, '', '')

    print('Done with difficulty 2')


# -----------------------------------------------------------------------------------------------------------------
# Difficulty 1
def difficulty_1(sessions, requested_articles):
    for session in sessions:
        for nb_articles in requested_articles:
            query_performance(session[0], 1, session[2], session[1], nb_articles, '', '',
                              '', '', '')

    print('Done with difficulty 1')


if __name__ == '__main__':
    # Difficulty is based on the complexity of the query.
    # 5 - Full query with five search terms
    # 4 - Full query with three search term
    # 3 - Full query with one search term
    # 2 - Query with missing content, user_topics and unwanted_user_topics (only pre configured topics)
    # 1 - Language only query

    content_difficulty_5 = ""
    content_difficulty_4 = 'Trump Melania'
    content_difficulty_3 = 'Trump'
    wanted_topics = '10'
    unwanted_topics = '13 14 15'
    wanted_user_topics = 'White House Dancing'
    unwanted_user_topics = 'Obama'

    engine10k = database.create_engine('mysql://root:Svx83mcf@localhost/zeeguu_10k?charset=utf8')
    Session10k = sessionmaker(bind=engine10k)
    session10k = Session10k()

    engine100k = database.create_engine('mysql://root:Svx83mcf@localhost/zeeguu_100k?charset=utf8')
    Session100k = sessionmaker(bind=engine100k)
    session100k = Session100k()

    engine1000k = database.create_engine('mysql://root:Svx83mcf@localhost/zeeguu?charset=utf8')
    Session1000k = sessionmaker(bind=engine1000k)
    session1000k = Session1000k()

    title_of_csv = 'Mircea_test.csv'

    session_lst = [(session10k, '10k', 'zeeguu_articles10k'), (session100k, '100k', 'zeeguu_articles100k'),
                   (session1000k, '1000k', 'zeeguu_articles')]
    requested_articles_lst = [10, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
    difficulty_5(session_lst, requested_articles_lst)
    # difficulty_4(session_lst, requested_articles_lst)
    # difficulty_3(session_lst, requested_articles_lst)
    # difficulty_2(session_lst, requested_articles_lst)
    # difficulty_1(session_lst, requested_articles_lst)