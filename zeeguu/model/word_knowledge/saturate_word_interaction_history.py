from datetime import datetime

import zeeguu
from zeeguu import model
from zeeguu.model import User, RSSFeed, Url, Article, DomainName, Bookmark, UserArticle, Text, UserWord
from nltk import word_tokenize
from zeeguu.model.word_knowledge.word_interaction_history import WordInteractionHistory, WordInteractionEvent

import re

LOG_CONTEXT = "FEED RETRIEVAL"

session = zeeguu.db.session

for ua in UserArticle.query.all():

    if ua.opened == None:
        continue

    user = ua.user
    text = ua.article.content

    #words = word_tokenize(text)

    words = re.findall(r'[a-zA-Z]+', text)

    words = [w.lower() for w in words]
    unique_words = set(words)

    bookmarks = Bookmark.query.join(Text).filter(Bookmark.user == user).filter(Text.url == ua.article.url).all()
    #translated_userWords = set([bm.origin.word.lower() for bm in bookmarks])



    #additional checks whether article is read



    for w in unique_words:
        userWord = UserWord.find_or_create(session, w, ua.article.language)
        wih = WordInteractionHistory.find_or_create(user, userWord)

        bookmarked = False
        for bm in bookmarks:
            if bm.origin.word.lower() == w:
                wih.add_event(WordInteractionEvent.CLICKED, bm.time)
                bookmarked = True
                break

        if not bookmarked:
            wih.add_event(WordInteractionEvent.NOT_CLICKED, ua.opened)





        wih.save_to_db(session)



    #go through bookmarks
    # for each bookmark extract user and textid
    # retrieve content of testid and create a set of words
    # for each word determine whether it has been translated (use bookmark)
    # apply unique labels for words translated and not translated

    # for each word determine whether it has a history otherwise create a new one
    # apply changes in history for the word

    # save and repeat for next bookmark
