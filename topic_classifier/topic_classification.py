import csv
import os

import zeeguu_core
from elastic import elastic_query_builder
from operator import itemgetter
from elasticsearch import Elasticsearch
from topic_classifier.more_like_this_query import build_more_like_this_query
from elastic.converting_from_mysql import find_topics
from zeeguu_core.model import article, Topic
from elastic.elastic_query_builder import build_elastic_query
from sqlalchemy.orm import sessionmaker
from zeeguu_core.settings import ES_ZINDEX, ES_CONN_STRING
import sqlalchemy as database
from zeeguu_core.model.article import article_topic_map, Article

es = Elasticsearch([ES_CONN_STRING])
DB_URI = zeeguu_core.app.config["SQLALCHEMY_DATABASE_URI"]
engine = database.create_engine(DB_URI, encoding='utf8')
Session = sessionmaker(bind=engine)
session = Session()


def find_results_from_string():
    articles = session.query(Article).filter(
        Article.id.in_(session.query(article_topic_map.c.article_id))).all()
    for article in articles:
        get_more_like_this_results(article)


def get_more_like_this_results(article):
    query_body = build_more_like_this_query(10, article.content, article.language)

    res = es.search(index=ES_ZINDEX, body=query_body)
    for result in res['hits']['hits']:
        if not result['_source']['topics']:
            assign_topic(result, article)


def assign_topic(result, article):
    topics = ""

    for t in article.topics:
        topics = topics + str(t.title) + " "

    topics = topics.rstrip()

    res = es.update(index=ES_ZINDEX, doc_type='_doc', id=result['_id'], body={"doc": {"topics": topics}})
    print(res['result'] + str(result['_id']))

    write_results_to_csv(result['_id'], topics, result['_score'], result['_source']['title'])


def write_results_to_csv(article_id, best_topic, best_score, title):
    file_name = 'best_topics_title.csv'
    file_exists = os.path.isfile(file_name)

    with open("best_topics_title.csv", 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Article ID', "Best Topic", "Best Topic Score", "Title"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()

        writer.writerow({'Article ID': article_id,
                         'Best Topic': best_topic, 'Best Topic Score': best_score, 'Title': title})


# def get_best_topic(response):
#     topics = {}
#     for hit in response['hits']['hits']:
#         score = hit['_score']
#         if 'topics' in hit['_source']:
#             for topic in hit['_source']['topics'].split():
#                 if topic not in topics:
#                     topics[topic] = score
#                 else:
#                     topics[topic] += score
#
#     sorted_topics = {}
#     if len(topics) > 0:
#         sorted_topics = sorted(topics.items(), key=itemgetter(1), reverse=True)
#
#     return sorted_topics


# def assign_topic(article, sorted_topics):
#     if not sorted_topics:
#         return
#
#     if len(sorted_topics) is 1:
#         best_topic = sorted_topics[0][0]
#         best_score = sorted_topics[0][1]
#         second_best_topic = 0
#         second_best_topic_score = 0
#     else:
#         best_topic = sorted_topics[0][0]
#         best_score = sorted_topics[0][1]
#         second_best_topic = sorted_topics[1][0]
#         second_best_topic_score = sorted_topics[1][1]
#
#     res = es.update(index=ES_ZINDEX, doc_type='_doc', id=article.id, body={"doc": {"topics": sorted_topics[0][0]}})
#     print(res['result'] + str(article.id))
#
#
#     write_results_to_csv(article.id, best_topic, best_score,
#                          second_best_topic, second_best_topic_score)


# def write_results_to_csv(article_id, best_topic, best_score, second_best_topic, second_best_topic_score):
#     file_name = 'best_topics_title.csv'
#     file_exists = os.path.isfile(file_name)
#
#     with open("best_topics_title.csv", 'a', newline='', encoding='utf-8') as csvfile:
#         fieldnames = ['Article ID', "Best Topic", "Best Topic Score", "Second Best Topic",
#                       "Second Best Topic Score"]
#         writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
#         if not file_exists:
#             writer.writeheader()
#
#         writer.writerow({'Article ID': article_id,
#                          'Best Topic': best_topic, 'Best Topic Score': best_score,
#                          'Second Best Topic': second_best_topic, 'Second Best Topic Score': second_best_topic_score})


def main():
    find_results_from_string()


if __name__ == '__main__':
    main()