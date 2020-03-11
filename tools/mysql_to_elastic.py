# coding=utf-8
import sqlalchemy as database
from sqlalchemy import func
from elasticsearch import Elasticsearch
from datetime import datetime
import zeeguu_core
from sqlalchemy.orm import sessionmaker, relationship, backref
from zeeguu_core.model import Topic, Article, Language
from zeeguu_core.model.article import article_topic_map as ATM

db = zeeguu_core.db
es = Elasticsearch(['127.0.0.1:9200'])

# TODO: Remove user / pass from db string
engine = database.create_engine('mysql://root:Svx83mcf@localhost/zeeguu?charset=utf8')
# create a configured "Session" class
Session = sessionmaker(bind=engine)
session = Session()


def main():
    max_id = session.query(func.max(Article.id)).first()[0]
    for i in range(0, max_id, 5000):
        for article in session.query(Article).order_by(Article.id).limit(5000).offset(i):
            topics = find_topics(article.id)
            language = find_language(article.language_id)
            doc = {
                'title': article.title,
                'author': article.authors,
                'content': article.content,
                'summary': article.summary,
                'word_count': article.word_count,
                'published_time': article.published_time,
                'topics': topics,
                'language': language,
                'fk_difficulty': article.fk_difficulty
            }
            res = es.index(index="zeeguu_articles100k", id=article.id, body=doc)
            if article.id % 1000 == 0:
                print(res['result'] + str(article.id))


def find_topics(article_id):
    article_topic = session.query(Topic).join(ATM).filter(ATM.c.article_id == article_id)
    topics = ""
    for t in article_topic:
        topics = topics + str(t.id) + " "

    return topics.rstrip()


def find_language(lang_id):
    article_lang = session.query(Language).filter(Language.id == lang_id).first()
    return article_lang.name


if __name__ == '__main__':
    main()
