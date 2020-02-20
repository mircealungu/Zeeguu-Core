# coding=utf-8
import sqlalchemy as database
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UnicodeText, Table
from elasticsearch import Elasticsearch
from datetime import datetime
import zeeguu_core
from sqlalchemy.orm import sessionmaker, relationship, backref
from zeeguu_core.model import Article
from zeeguu_core.model import Topic
from zeeguu_core.model import Article
from zeeguu_core.model.article import article_topic_map

db = zeeguu_core.db
es = Elasticsearch(['127.0.0.1:9200'])

#TODO: Remove user / pass

engine = database.create_engine('mysql://root:Svx83mcf@localhost/zeeguu?charset=utf8')
# create a configured "Session" class
Session = sessionmaker(bind=engine)

session = Session()

for topic in session.query(Article).join(article_topic_map).filter(article_topic_map.c.article_id == ):
    print(article)

for article in session.query(Article).order_by(Article.id):
    doc = {
        'title': article.title,
        'author': article.authors,
        'content': article.content,
        'summary': article.summary,
        'word_count': article.word_count,
        'published_time': article.published_time
    }
    res = es.index(index="zeeguu_articles", id=article.id, body=doc)
    print(res['result'] + str(article.id))

#res = es.get(index="test", id=1)
#print(res['result'])