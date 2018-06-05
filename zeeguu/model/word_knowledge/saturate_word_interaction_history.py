from datetime import datetime, timedelta

import zeeguu
from zeeguu import model
from zeeguu.model import User, RSSFeed, Url, Article, DomainName, Bookmark, UserArticle, Text, \
    UserWord, ExerciseBasedProbability, Exercise, ExerciseOutcome, UserActivityData, UserReadingSession
from zeeguu.model.bookmark import bookmark_exercise_mapping
from nltk import word_tokenize
from zeeguu.model.word_knowledge.word_interaction_history import WordInteractionHistory, WordInteractionEvent
from zeeguu.constants import WIH_READ_NOT_CLICKED_IN_SENTENCE, WIH_READ_NOT_CLICKED_OUT_SENTENCE,\
     WIH_READ_CLICKED, UMR_USER_FEEDBACK_ACTION
from sqlalchemy.sql import func

import re

LOG_CONTEXT = "FEED RETRIEVAL"
ARTICLE_FULLY_READ = "finished%"
LONG_TIME_IN_THE_PAST = "2000-01-01T00:00:00"

session = zeeguu.db.session

def extract_words_from_text(text):#Tokenize the words and create a set of unique words
    words = re.findall(r'[a-zA-Z]+', text)
    words = [w.lower() for w in words]
    return set(words)

def get_fully_read_timestamps(user_article):
    """
        Find all the fully read dates of an article by a user

        return: list of timestamps
    """

    url = user_article.article.url.as_string()

    query = UserActivityData.query.filter(UserActivityData.user_id == user_article.user_id)
    query = query.filter(UserActivityData.event == UMR_USER_FEEDBACK_ACTION)
    query = query.filter(UserActivityData.value == url)
    query = query.filter(UserActivityData.extra_data.like(ARTICLE_FULLY_READ))

    full_read_activity_results = query.all()

    if full_read_activity_results:
        return full_read_activity_results.time
    else:
        return full_read_activity_results

def process_bookmarked_sentences(user_article, start_time=LONG_TIME_IN_THE_PAST, end_time=datetime.now()):
    """
        Process all bookmarks for the user_article within the specified times

        Parameters:
        user_article = user_article class object
        start_time = datetime from which to take bookmarks
        end_time = datetime of final bookmark to process

        returns: list of processed bookmarks
    """
    user = user_article.user

    #Get all the bookmarks for the specified article and dates
    query = Bookmark.query.join(Text).filter(Bookmark.user == user).filter(Text.url == user_article.article.url)
    query = query.filter(Bookmark.time >= start_time).filter(Bookmark.time <= end_time)
    bookmarks = query.order_by(Bookmark.time).all()
    
    for bookmark in bookmarks:

        # reading_sessions = UserReadingSession.find_by_user_and_article(user=user.id, article=user_article.article_id)
        
        # #Find corresponding reading session based on the date of the timestamp
        # for read_session in reading_sessions:
        #     session_start_time = read_session.start_time
        #     session_end_time = read_session.start_time + timedelta(seconds=read_session.duration/1000)

        #     # if bookmark.time > session_start_time and bookmark.time < session_end_time:
        #     #     current_read_session = read_session
        #     #     break

        # #If no reading session exists
        session_start_time = Bookmark.time - timedelta(minutes=2)

        #Find previous bookmarks in same reading session and article
        query = Bookmark.query.join(Text).filter(Bookmark.user == user).filter(Text.url == user_article.article.url)
        query = query.filter(Bookmark.time > session_start_time).filter(Bookmark.time < bookmark.time)
        bookmarks_in_same_session = query.order_by(Bookmark.time).all()
        same_session_bmk_times = []
        same_session_bmk_words = [bookmark.origin.word]
        for bmk in bookmarks_in_same_session: 
            same_session_bmk_times.append(int(bmk.time.strftime("%s")))
            same_session_bmk_words.append(bmk.origin.word)
        
        #Get text in the sentece of the bookmark
        sentence = Text.query.filter(Text.id == bookmark.text_id).one().content

        # Get unique words in sentence
        unique_words_in_sentence = extract_words_from_text(sentence)

        for word in unique_words_in_sentence:

            #Get UserWord object
            user_word = UserWord.find_or_create(session=session, _word=word, language=user_article.article.language)

            #Find a WordInteractionHistory
            word_interaction_history = WordInteractionHistory.find_or_create(user=user, word=user_word)

            #Find if the word has been inserted by previous bookmarks in th same reading session
            word_history_events = word_interaction_history.interaction_history

            if word in same_session_bmk_words:
                event_type = WIH_READ_CLICKED
            else:
                event_type = WIH_READ_NOT_CLICKED_IN_SENTENCE
                    
            if word_history_events:
                for event in word_history_events:
                    
                    #If there is a match then update the timestamp
                    if event.seconds_since_epoch in same_session_bmk_times:
                        event.seconds_since_epoch = int(bookmark.time.strftime("%s"))
                        #If the precedence order of events is higher, update the event type (clicked > not clicked in sentence)
                        if word in same_session_bmk_words:
                            event.event_type = WIH_READ_CLICKED
                    else:
                        #Create a new event
                        word_interaction_history.add_event_insert(event_type, bookmark.time)
            else:
                
                word_interaction_history.add_event_insert(event_type, bookmark.time)
            
            word_interaction_history.save_to_db(session)

    return bookmarks

#==============================READING================================
#Fill reading sessions word history information
for ua in UserArticle.query.all():

    if ua.opened == None:
        continue

    user = ua.user
    text = ua.article.content
    print(ua.id)

    fully_read_dates = get_fully_read_timestamps(ua)

    #If the article has nos been marked as fully read, we only process the sentences of the bookmarks
    if not fully_read_dates:
        process_bookmarked_sentences(ua)
    else: #If article has been fully read

        #If article is fully read, process the remaning words as not read out of bookmarked sentence
        #NOTE: The article can be fully read multiple times, therefore we only consider the corresponding bookmarks

        #Get all the unique article words
        unique_words_in_article = extract_words_from_text(text)

        #For each fully read date, we process the corresponding bookmarked sentences
        previous_fully_read_date = LONG_TIME_IN_THE_PAST
        for fully_read_date in fully_read_dates:
            processed_bookmarks = process_bookmarked_sentences(ua, previous_fully_read_date, fully_read_date)
            previous_fully_read_date = fully_read_date

            #Extract words from bookmarked sentences
            for bookmark in processed_bookmarks:

                #Get text in the sentece of the bookmark
                sentence = Text.query.filter(Text.id == bookmark.text_id).one().content

                # Get unique words in sentence
                unique_words_in_sentence = extract_words_from_text(sentence)

                #Remove already processed words
                unique_words_in_article = unique_words_in_article.difference(unique_words_in_sentence)

            #Insert remaining words as not clicked out of sentence
            for word in unique_words_in_article:
                user_word = UserWord.find_or_create(session=session, _word=word, language=ua.article.language)
                word_interaction_history = WordInteractionHistory.find_or_create(user=user, word=user_word)
                word_interaction_history.add_event_insert(WIH_READ_NOT_CLICKED_OUT_SENTENCE, fully_read_date)
                
                word_interaction_history.save_to_db(session)



#==============================EXERCISES================================
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

#TODO: store last processed exercise id



    #go through bookmarks
    # for each bookmark extract user and textid
    # retrieve content of testid and create a set of words
    # for each word determine whether it has been translated (use bookmark)
    # apply unique labels for words translated and not translated

    # for each word determine whether it has a history otherwise create a new one
    # apply changes in history for the word

    # save and repeat for next bookmark
