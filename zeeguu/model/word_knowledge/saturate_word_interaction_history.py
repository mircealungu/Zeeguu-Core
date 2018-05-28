from datetime import datetime

import zeeguu
from zeeguu import model
from zeeguu.model import User, RSSFeed, Url, Article, DomainName, Bookmark, UserArticle, Text, UserWord, ExerciseBasedProbability, Exercise, ExerciseOutcome
from zeeguu.model.bookmark import bookmark_exercise_mapping
from nltk import word_tokenize
from zeeguu.model.word_knowledge.word_interaction_history import WordInteractionHistory, WordInteractionEvent

import re

LOG_CONTEXT = "FEED RETRIEVAL"

session = zeeguu.db.session

for ua in UserArticle.query.all():
    break
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



    #todo: additional checks whether article is read

    # reduce bookmarks to unique words and earliest translations
    bookmarked_words = dict()
    for bm in bookmarks:
        word = bm.origin.word.lower()
        if word not in bookmarked_words or bookmarked_words[word] > bm.time:
            bookmarked_words[word] = bm.time

    # add Interaction event
    for word, time in bookmarked_words.items():
        userWord = UserWord.find_or_create(session, word, ua.article.language)
        wih = WordInteractionHistory.find_or_create(user, userWord)
        if not wih.time_exists(time):
            wih.add_event("CLICKED", time)
            wih.save_to_db(session)

    # all other unique words are stored as NOT_CLICKED
    for w in unique_words.difference(bookmarked_words.keys()):

        userWord = UserWord.find_or_create(session, w, ua.article.language)

        wih = WordInteractionHistory.find_or_create(user, userWord)

        if not wih.time_exists(ua.opened):
            wih.add_event("NOTCLICKED", ua.opened)
            wih.save_to_db(session)

# words encountered in exercises
bmex_mapping = data = session.query(bookmark_exercise_mapping).all()
print(bmex_mapping)


for bm_id, ex_id in bmex_mapping:

    try:
        bm = Bookmark.query.filter(Bookmark.id == bm_id).one()
        ex = Exercise.query.filter(Exercise.id == ex_id).one()
    except:
        print("bookmark or exercise not found")
        continue

    userWord = UserWord.find_or_create(session, bm.origin.word.lower(), bm.origin.language)


    wih = WordInteractionHistory.find_or_create(bm.user, userWord)
    if not wih.time_exists(ex.time):
        wih.add_event(ex.outcome.outcome, ex.time)
        wih.save_to_db(session)





    #go through bookmarks
    # for each bookmark extract user and textid
    # retrieve content of testid and create a set of words
    # for each word determine whether it has been translated (use bookmark)
    # apply unique labels for words translated and not translated

    # for each word determine whether it has a history otherwise create a new one
    # apply changes in history for the word

    # save and repeat for next bookmark
