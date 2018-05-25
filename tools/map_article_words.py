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
filter_fr = ['le', 'la', 'est', 'en', 'un', 'a', 'l', 'du', 'de', 'les']

filter_general.extend(filter_fr)
starting_time = time.time()

for article in articles:
    title = article.title
    address = article.url.as_string()
    all_words = []

    url = urlparse(address)
    subdomain = url.netloc.split('.')[0]
    title_words = title.split()

    all_words.append(subdomain)
    all_words.extend(re.split('; |, |\*|-|%20|/', url.path))
    all_words.extend(title_words)

    all_words = list(filter(None, all_words))
    for word in all_words:
        word = word.strip()
        word = word.strip(":,\,,\",?,!")
        if word in filter_general:
            filtered_general += 1
        elif len(word) < 3 or len(word) > 29:
            filtered_length += 1
        elif any(char in range(9) for char in word):
            filtered_digits += 1
        else:
            article_word = ArticleWord.find_or_create(session, word)
            article_word.add_article(article)
            session.add(article_word)
        word_count += 1
        if word_count % 1000 == 0:
            print("another 1000 words added")

    article_count += 1
    if article_count % 1000 == 0:
        print("another 1000 articles done and committed")
        session.commit()

ending_time = time.time()
print(f'In a total of {ending_time - starting_time} seconds :')
print(f'A total of {article_count} articles handled')
print(f'A total of {word_count} words handled')
print(f'A total of {filtered_general} words filtered general')
print(f'A total of {filtered_length} words filtered length')
print(f'A total of {filtered_digits} words filtered digit')





