#!/usr/bin/env python


"""

    Script that goes through all the articles in the database,
    gets all the words from an article title and url, and
    finally puts these words in a separate table with a map
    from words to articles.


"""

import zeeguu
from zeeguu.model.article import Article
from zeeguu.model.article_word import ArticleWord
from nltk.corpus import stopwords
from urllib.parse import urlparse
import time
import re

session = zeeguu.db.session
word_count = 0
article_count = 0
filtered_general = 0
filtered_length = 0
filtered_digits = 0
articles = Article.query.all()

filter_general = ['www', '', ' ']
starting_time = time.time()

all_words_list = []

article_words = ArticleWord.query.order_by(ArticleWord.id.desc()).all()
result = zeeguu.db.engine.execute("SELECT min(article_id) FROM article_word_map").fetchone()
# This is kind of an awkward way of finding the last tagged article,
# though it definitely works as it check the last 100 words and all the
# articles associated to it.
min_id = result[0]
print(f'#### ID TO START AT: {min_id} ####')

# Reverse the articles to start at the most recent ones
articles.reverse()

print(f'#### STARTING MAIN LOOP ####')
for article in articles:
    if article.id > min_id:
        print(f'#### SKIPPED article with id: {article.id} ####')
        continue
    print(f'#### PROCESSING ARTICLE WITH ID: {article.id} ####')
    title = article.title
    address = article.url.as_string()
    language = article.language.name.lower()
    all_words = []

    url = urlparse(address)
    subdomain = url.netloc.split('.')[0]
    title_words = title.split()

    all_words.append(subdomain)
    all_words.extend(re.split('; |, |\*|-|%20|/', url.path))
    all_words.extend(title_words)

    all_words = list(filter(None, all_words))
    for word in all_words:
        article_word_obj = None
        word = word.strip()
        word = word.strip(":,\,,\",?,!,<,>")
        word = word.lower()
        if word in filter_general:
            filtered_general += 1
        elif len(word) < 3 or len(word) > 29:
            filtered_length += 1
        elif all(char in range(9) for char in word):
            filtered_digits += 1
        elif word in set(stopwords.words(language)):
            filtered_general += 1
        else:
            for article_word in all_words_list:
                if word == article_word.word:
                    article_word_obj = article_word
                    break
            if article_word_obj is None:
                article_word_obj = ArticleWord.find_or_create(session, word)
            article_word_obj.add_article(article)
            session.add(article_word_obj)
            all_words_list.append(article_word_obj)
        word_count += 1
        if word_count % 1000 == 0:
            print("another 1000 words added")
            print(f'That took {time.time() - starting_time} seconds...')

    article_count += 1
    if article_count % 1000 == 0:
        print("another 1000 articles done and committed")
        print(f'That took {time.time() - starting_time} seconds...')
        session.commit()

ending_time = time.time()
print(f'In a total of {ending_time - starting_time} seconds :')
print(f'A total of {article_count} articles handled')
print(f'A total of {word_count} words handled')
print(f'A total of {filtered_general} words filtered general')
print(f'A total of {filtered_length} words filtered length')
print(f'A total of {filtered_digits} words filtered digit')





