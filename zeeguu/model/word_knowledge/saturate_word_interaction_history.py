from datetime import datetime

import zeeguu
from zeeguu import model
from zeeguu.model import User, RSSFeed, Url, Article, DomainName, Bookmark, UserArticle, Text, UserWord, ExerciseBasedProbability, Exercise, ExerciseOutcome
from zeeguu.model.bookmark import bookmark_exercise_mapping
from nltk import word_tokenize
from zeeguu.model.word_knowledge.word_interaction_history import WordInteractionHistory, WordInteractionEvent
from zeeguu.constants import WIH_READ_NOT_CLICKED, WIH_READ_CLICKED
from sqlalchemy.sql import func

import re

LOG_CONTEXT = "FEED RETRIEVAL"

session = zeeguu.db.session

def extract_words_from_text(text):#Tokenize the words and create a set of different words
    words = re.findall(r'[a-zA-Z]+', text)
    words = [w.lower() for w in words]
    return set(words)

#Fill reading sessions word history information
for ua in UserArticle.query.all():

    if ua.opened == None:
        continue

    user = ua.user
    try:
        text = ua.article.content
        
        #Get all the bookmarks for the specified article
        bookmarks = Bookmark.query.join(Text).filter(Bookmark.user == user).filter(Text.url == ua.article.url).order_by(Bookmark.id).all()

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
            wih.add_event_insert(WIH_READ_CLICKED, time)
            wih.save_to_db(session)

        if ua.liked:

            #all other unique words are stored as NOT_CLICKED
            unique_words = extract_words_from_text(text)
            for w in unique_words.difference(bookmarked_words.keys()):

                userWord = UserWord.find_or_create(session, w, ua.article.language)
                wih = WordInteractionHistory.find_or_create(user, userWord)

                if not wih.time_exists(ua.opened):
                    wih.add_event_insert(WIH_READ_NOT_CLICKED, ua.opened)
                    wih.save_to_db(session)

        else: #Consider only the words up to the sentence with last translation

            if bookmarks:
                #Find the last translated word
                last_bookmark = bookmarks[len(bookmarks)-1]

                #Find the text in which the word is located and extract all the words up to that sentence
                text = Text.query.filter(Text.id == last_bookmark.text_id).one()
                sentence = text.content
                article_text = ua.article.content

                index_last_read_sentence = article_text.find(sentence) + len(sentence)

                for w in extract_words_from_text(article_text[0:index_last_read_sentence]):

                    userWord = UserWord.find_or_create(session, w, ua.article.language)
                    wih = WordInteractionHistory.find_or_create(user, userWord)

                    if not wih.time_exists(ua.opened):
                        wih.add_event_insert(WIH_READ_NOT_CLICKED, ua.opened)
                        wih.save_to_db(session)

    except: #Some error while accessing the article
        continue



# words encountered in exercises
bmex_mapping = data = session.query(bookmark_exercise_mapping).all()
# print(bmex_mapping)


for bm_id, ex_id in bmex_mapping:
    break
    try:
        bm = Bookmark.query.filter(Bookmark.id == bm_id).one()
        ex = Exercise.query.filter(Exercise.id == ex_id).one()
    except:
        print("bookmark or exercise not found")
        continue

    word_interaction_event = WordInteractionEvent.encodeExerciseResult(ex.outcome_id, ex.source_id)

    userWord = UserWord.find_or_create(session, bm.origin.word.lower(), bm.origin.language)
    wih = WordInteractionHistory.find_or_create(bm.user, userWord)
    wih.add_event_insert(word_interaction_event, ex.time)
    wih.save_to_db(session)





    #go through bookmarks
    # for each bookmark extract user and textid
    # retrieve content of testid and create a set of words
    # for each word determine whether it has been translated (use bookmark)
    # apply unique labels for words translated and not translated

    # for each word determine whether it has a history otherwise create a new one
    # apply changes in history for the word

    # save and repeat for next bookmark
