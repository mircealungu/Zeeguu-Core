import os

from elasticsearch import Elasticsearch
import sqlalchemy as database
from sqlalchemy.orm import sessionmaker
from zeeguu_core.model import full_query
from comparison.mysqlFullText import build_mysql_query, old_mysql_query
from timeit import default_timer as timer
from zeeguu_core.model import Language
import csv
from zeeguu_core.elasticSettings import settings

es = Elasticsearch([settings['ip']])


def query_performance(mysql, difficulty, index, size_of_index, size, content, topics,
                      unwanted_topics, user_topics, unwanted_user_topics):
    language = Language("de", "German")
    language.id = 3

    elastic_query_body = full_query(size, content, topics, unwanted_topics,
                            user_topics, unwanted_user_topics, language, 100, 0)
    mysql_query_full_text = build_mysql_query(mysql, size, content, topics, unwanted_topics,
                                    user_topics, unwanted_user_topics, language, 100, 0)
    mysql_query_old = old_mysql_query(mysql, size, content, topics, unwanted_topics,
                                    user_topics, unwanted_user_topics, language, 100, 0)

    # elastic_time_lst = []
    # elastic_returned_articles = []
    # for j in range(10):
    #     start = timer()
    #     res = es.search(index=index, body=elastic_query_body)
    #     elastic_returned_articles.append(len(res['hits'].get('hits')))
    #     end = timer()
    #     elastic_time_lst.append(end - start)
    #
    # write_results_to_csv(difficulty, size_of_index + " elastic", average_time(elastic_time_lst), size,
    #                      average(elastic_returned_articles))

    # #MySQL Full Text
    mysql_time_lst = []
    mysql_returned_articles = []
    for i in range(10):
        start = timer()
        result = mysql_query_full_text.all()
        mysql_returned_articles.append(len(result))
        end = timer()
        mysql_time_lst.append(end-start)

    write_results_to_csv(difficulty, size_of_index + " MySQL Full Text", average_time(mysql_time_lst),
                         size, average(mysql_returned_articles))

    # # MySQL Old Version
    # mysql_time_lst = []
    # mysql_returned_articles = []
    # for i in range(10):
    #     start = timer()
    #     result = mysql_query_old.all()
    #     mysql_returned_articles.append(len(result))
    #     end = timer()
    #     mysql_time_lst.append(end - start)
    #
    # write_results_to_csv(difficulty, size_of_index + " MySQL Old Version", average_time(mysql_time_lst),
    #                      size, average(mysql_returned_articles))


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


# ---------------------------------------------------------------------------------------------------------------------
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


# -------------------------------------------------------------------------------------------------------------------
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
    # 5 - Full query with three search terms
    # 4 - Full query with two search term
    # 3 - Full query with one search term
    # 2 - Query with missing content, user_topics and unwanted_user_topics (only pre configured topics)
    # 1 - Language only query

    content_difficulty_5 = "trump"
    content_difficulty_4 = 'nutty frame'
    content_difficulty_3 = 'nutty'
    wanted_topics = ''
    unwanted_topics = ''
    wanted_user_topics = ''
    unwanted_user_topics = ''

    # engine10k = database.create_engine('mysql://root:Svx83mcf@localhost/zeeguu_10k?charset=utf8')
    # Session10k = sessionmaker(bind=engine10k)
    # session10k = Session10k()
    #
    # engine100k = database.create_engine('mysql://root:Svx83mcf@localhost/zeeguu_100k?charset=utf8')
    # Session100k = sessionmaker(bind=engine100k)
    # session100k = Session100k()

    engine1000k = database.create_engine('mysql://root:1234@localhost/zeeguu?charset=utf8')
    Session1000k = sessionmaker(bind=engine1000k)
    session1000k = Session1000k()

    title_of_csv = 'user_30_test_trump_german_mysql.csv'

    # session_lst = [(session10k, '10k', 'zeeguu_articles10k'), (session100k, '100k', 'zeeguu_articles100k'),
    #                (session1000k, '1000k', 'zeeguu_articles')]

    session_lst = [(session1000k, '1000k', settings["index"])]

    # requested_articles_lst = [10, 20, 50, 100]
    requested_articles_lst = [100]
    difficulty_5(session_lst, requested_articles_lst)
    # difficulty_4(session_lst, requested_articles_lst)
    # difficulty_3(session_lst, requested_articles_lst)
    # difficulty_2(session_lst, requested_articles_lst)
    # difficulty_1(session_lst, requested_articles_lst)
