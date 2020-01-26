import re
from datetime import datetime

import sqlalchemy
from sqlalchemy import Column, ForeignKey, Integer, Table
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound
from zeeguu_core.constants import SIMPLE_TIME_FORMAT, JSON_TIME_FORMAT
from zeeguu_core.model import Article

from wordstats import Word

import zeeguu_core
from zeeguu_core.model.exercise import Exercise
from zeeguu_core.model.exercise_outcome import ExerciseOutcome
from zeeguu_core.model.exercise_source import ExerciseSource
from zeeguu_core.model.language import Language
from zeeguu_core.model.text import Text
from zeeguu_core.model.url import Url
from zeeguu_core.model.user import User
from zeeguu_core.model.user_word import UserWord
from zeeguu_core.util.timer_logging_decorator import time_this

db = zeeguu_core.db

CORRECTS_IN_A_ROW_FOR_LEARNED = 4
CORRECTS_IN_DISTINCT_DAYS_FOR_LEARNED = 4

bookmark_exercise_mapping = Table('bookmark_exercise_mapping',
                                  db.Model.metadata,
                                  Column('bookmark_id', Integer,
                                         ForeignKey('bookmark.id')),
                                  Column('exercise_id', Integer,
                                         ForeignKey('exercise.id'))
                                  )

WordAlias = db.aliased(UserWord, name="translated_word")


class Bookmark(db.Model):
    __table_args__ = {'mysql_collate': 'utf8_bin'}

    id = db.Column(db.Integer, primary_key=True)

    origin_id = db.Column(db.Integer, db.ForeignKey(UserWord.id), nullable=False)
    origin = db.relationship(UserWord, primaryjoin=origin_id == UserWord.id)

    translation_id = db.Column(db.Integer, db.ForeignKey(UserWord.id), nullable=False)
    translation = db.relationship(UserWord, primaryjoin=translation_id == UserWord.id)

    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    user = db.relationship(User)

    text_id = db.Column(db.Integer, db.ForeignKey(Text.id))
    text = db.relationship(Text)

    time = db.Column(db.DateTime)

    exercise_log = relationship(Exercise,
                                secondary="bookmark_exercise_mapping",
                                order_by="Exercise.id")

    starred = db.Column(db.Boolean, default=False)

    learned = db.Column(db.Boolean, default=False)

    fit_for_study = db.Column(db.Boolean)

    learned_time = db.Column(db.DateTime)

    def __init__(self, origin: UserWord, translation: UserWord, user: 'User',
                 text: str, time: datetime):
        self.origin = origin
        self.translation = translation
        self.user = user
        self.time = time
        self.text = text
        self.stared = False
        self.fit_for_study = self._fit_for_study()

    def __repr__(self):
        return "Bookmark[{3} of {4}: {0}->{1} in '{2}...']\n". \
            format(self.origin.word, self.translation.word,
                   self.text.content[0:10], self.id, self.user_id)

    def serializable_dictionary(self):
        return dict(
            origin=self.origin.word,
            translation=self.translation.word,
            context=self.text.content
        )

    def add_new_exercise(self, exercise):
        self.exercise_log.append(exercise)

    def translations_rendered_as_text(self):
        return self.translation.word

    def content_is_not_too_long(self):
        return len(self.text.content) < 60

    def events_prevent_further_study(self):
        from zeeguu_core.model.smartwatch.watch_interaction_event import \
            WatchInteractionEvent
        events_for_self = WatchInteractionEvent.events_for_bookmark(self)
        return any([x.prevents_further_study() for x in events_for_self])

    def origin_same_as_translation(self):
        try:
            return self.origin.word.lower() == self.translation.word.lower()
        except:
            print("missing word for bookmark with id {0}".format(self.id))
            return False

    def is_subset_of_larger_bookmark(self):
        """
            if the user translates a superset of this sentence
        """
        all_bookmarks_in_text = Bookmark.find_all_for_text_and_user(self.text, self.user)

        for each in all_bookmarks_in_text:
            if each != self:
                if self.origin.word in each.origin.word:
                    return True
        return False

    def multiword_origin(self):
        return len(self.origin.word.split(" ")) > 1

    def origin_word_count(self):
        return len(self.origin.word.split(" "))

    def multiple_bookmarks_for_same_context(self):
        return len(self.text.all_bookmarks(self))

    def quality_top_bookmark(self):
        """

            used in the top bookmarks
            differs a bit from the exercises...
            although it could be decided to merge them in the future

        """
        context = self.text

        # word should not be too short
        if len(self.origin.word) < 5:
            return False

        # if there are other bookmarks in this context
        # it is not an ideal context, since the user
        # might not understand the context
        if self.multiple_bookmarks_for_same_context():
            return False

        # context not too long
        if len(context.content) > 140:
            return False

        return True

    def quality_bookmark(self):

        # If it's starred by the user, then it's good quality!
        if self.starred:
            zeeguu_core.log("starred -> good quality")
            return True

        # Else it just should not be bad quality!
        return not self.bad_quality_bookmark()

    def translation_in_context(self):
        if self.translation.word in self.text.content:
            return True

    def bad_quality_bookmark(self):
        # following are reasons that disqualify a bookmark from
        bad_quality = (

            # translation is same as origin
                self.origin_same_as_translation() or

                # origin which is subset of a larger origin
                (self.is_subset_of_larger_bookmark()) or

                # too long for our exercises
                (self.origin_word_count() > 3) or

                # very short words are also not great quality
                (len(self.origin.word) < 3)

                or
                # a too long context is not good either
                self.context_word_count() > 42

                or
                # a superset of translation same as origin...
                # happens in the case of some bugs in translation
                # where the translation is inserted in the text
                # till we fix it, we should not show this
                self.translation_in_context()

        )

        return bad_quality

    def update_fit_for_study(self, session=None):
        """
            Called when something happened to the bookmark,
             that requires it's "fit for study" status to be
              updated. Including:
              - starred / unstarred
              - exercise finished for the given bookmark
              - ...

        :param session:
        :return:
        """
        self.fit_for_study = self._fit_for_study()
        if session:
            session.add(self)

    @time_this
    def _fit_for_study(self):

        """

            A bookmark is good for study if it respects several
            properties:

            - has not been learned already
            - is a quality bookmark (which includes those starred by the user)
            - there's no feedback from the user that prevents us from showing it
            - the last outcome is not "too easy"

        :return:
        """

        last_outcome = self.latest_exercise_outcome()

        if last_outcome is None:
            return self.quality_bookmark() and not self.events_prevent_further_study()

        if self.is_learned_based_on_exercise_outcomes():
            return False

        return (self.quality_bookmark() and
                not last_outcome.too_easy() and
                not last_outcome.unknown_feedback() and
                not self.events_prevent_further_study())

    def add_new_exercise_result(self,
                                exercise_source: ExerciseSource,
                                exercise_outcome: ExerciseOutcome,
                                exercise_solving_speed):

        exercise = Exercise(exercise_outcome, exercise_source, exercise_solving_speed,
                            datetime.now())

        self.add_new_exercise(exercise)
        db.session.add(exercise)

        return exercise

    def report_exercise_outcome(self,
                                exercise_source: str,
                                exercise_outcome: str,
                                exercise_solving_speed,
                                db_session):

        from zeeguu_core.model import UserExerciseSession
        from zeeguu_core.word_scheduling.arts.bookmark_priority_updater import BookmarkPriorityUpdater

        new_source = ExerciseSource.find_or_create(db_session, exercise_source)
        new_outcome = ExerciseOutcome.find_or_create(db_session, exercise_outcome)

        exercise = self.add_new_exercise_result(new_source,
                                                new_outcome,
                                                exercise_solving_speed)
        db_session.add(exercise)
        db_session.commit()

        self.update_fit_for_study(db_session)
        self.update_learned_status(db_session)

        UserExerciseSession.update_exercise_session(exercise, db_session)
        BookmarkPriorityUpdater.update_bookmark_priority(db, self.user)

    def split_words_from_context(self):

        result = []
        bookmark_content_words = re.findall(r'(?u)\w+', self.text.content)
        for word in bookmark_content_words:
            if word.lower() != self.origin.word.lower():
                result.append(word)

        return result

    def context_word_count(self):
        words = self.split_words_from_context()
        return len(words)

    def json_serializable_dict(self, with_context=True, with_title=False):
        try:
            translation_word = self.translation.word
        except AttributeError as e:
            translation_word = ''
            zeeguu_core.log(f"Exception caught: for some reason there was no translation for {self.id}")
            print(str(e))

        word_info = Word.stats(self.origin.word,
                               self.origin.language.code)

        learned_datetime = str(self.learned_time.date()) if self.learned else ''

        created_day = "today" if self.time.date() == datetime.now().date() else ''

        bookmark_title = ""
        if with_title:
            try:
                bookmark_title = self.text.article.title
            except Exception as e:
                print(e)
                print(f"could not find article title for bookmark with id: {self.id}")

        result = dict(
            id=self.id,
            to=translation_word,
            from_lang=self.origin.language.code,
            to_lang=self.translation.language.code,
            title=bookmark_title,
            url=self.text.url.as_string(),
            origin_importance=word_info.importance,
            learned_datetime=self.most_recent_correct_dates(),
            origin_rank=word_info.rank if word_info.rank != 100000 else '',
            starred=self.starred if self.starred is not None else False,
            article_id=self.text.article_id if self.text.article_id else '',
            created_day=created_day,  # human readable stuff...
            time=self.time.strftime(JSON_TIME_FORMAT)
        )

        result["from"] = self.origin.word
        if with_context:
            result['context'] = self.text.content
        return result

    @classmethod
    def find_or_create(cls, session, user,
                       _origin: str, _origin_lang: str,
                       _translation: str, _translation_lang: str,
                       _context: str, _url: str, _url_title: str, article_id: int):
        """
            if the bookmark does not exist, it creates it and returns it
            if it exists, it ** updates the translation** and returns the bookmark object

        :param _origin:
        :param _context:
        :param _url:
        :return:
        """

        origin_lang = Language.find_or_create(_origin_lang)
        translation_lang = Language.find_or_create(_translation_lang)

        origin = UserWord.find_or_create(session, _origin, origin_lang)

        article = Article.query.filter_by(id=article_id).one()

        url = Url.find_or_create(session, article.url.as_string(), _url_title)

        context = Text.find_or_create(session, _context, origin_lang, url, article)

        translation = UserWord.find_or_create(session, _translation, translation_lang)

        now = datetime.now()

        try:
            # try to find this bookmark
            bookmark = Bookmark.find_by_user_word_and_text(user, origin,
                                                           context)

            # update the translation
            bookmark.translation = translation

        except sqlalchemy.orm.exc.NoResultFound as e:
            bookmark = cls(origin, translation, user, context, now)
        except Exception as e:
            raise e

        session.add(bookmark)
        session.commit()

        return bookmark

    @classmethod
    def find_by_specific_user(cls, user):
        return cls.query.filter_by(
            user=user
        ).all()

    @classmethod
    def find_all(cls):
        return cls.query.filter().all()

    @classmethod
    def find_all_for_text_and_user(cls, text, user):
        return Bookmark.query.filter_by(text=text, user=user).all()

    @classmethod
    def find_all_for_user_and_url(cls, user, url):
        return cls.query.join(Text).filter(Text.url == url).filter(Bookmark.user == user).all()

    @classmethod
    def find(cls, b_id):
        return cls.query.filter_by(
            id=b_id
        ).one()

    @classmethod
    def find_all_by_user_and_word(cls, user, word):
        return cls.query.filter_by(
            user=user,
            origin=word
        ).all()

    @classmethod
    def find_by_user_word_and_text(cls, user, word, text):
        return cls.query.filter_by(
            user=user,
            origin=word,
            text=text
        ).one()

    @classmethod
    def exists(cls, bookmark):
        try:
            cls.query.filter_by(
                origin_id=bookmark.origin.id,
                id=bookmark.id
            ).one()
            return True
        except NoResultFound:
            return False

    def latest_exercise_outcome(self):
        sorted_exercise_log_by_latest = sorted(self.exercise_log,
                                               key=lambda x: x.time,
                                               reverse=True)
        if sorted_exercise_log_by_latest:
            return sorted_exercise_log_by_latest[0].outcome
        else:
            return None

    def sorted_exercise_log(self):
        return sorted(self.exercise_log,
                      key=lambda x: x.time,
                      reverse=True)

    def compact_sorted_exercise_log(self):
        result = ""
        for ex in self.sorted_exercise_log():
            result += (f"{ex.time.day}/{ex.time.month} " +
                       f"{ex.outcome.outcome[:4]}   ")
        return result

    def most_recent_correct_dates(self):

        sorted_exercise_log = self.sorted_exercise_log()
        if len(sorted_exercise_log) == 0:
            return False, None

        # 3. Otherwise, count the number of corrects
        most_recent_corrects = []

        for exercise in sorted_exercise_log:
            if exercise.is_correct():
                most_recent_corrects.append(exercise)
            else:
                break

        distinct_days = []
        for exercise in most_recent_corrects:
            date = exercise.time.date()
            if date not in distinct_days:
                distinct_days.append(date)

        result = []
        for day in list(distinct_days)[:CORRECTS_IN_DISTINCT_DAYS_FOR_LEARNED]:
            result.append(day.strftime("%b.%d "))
        return " ".join(result)

    def is_learned_based_on_exercise_outcomes(self):
        """
        :return:
        """

        # 1. False if: We have no exercises
        sorted_exercise_log = self.sorted_exercise_log()
        if len(sorted_exercise_log) == 0:
            return False, None

        # We have at least one exercise
        last_exercise = sorted_exercise_log[0]

        # 2. True if: Last exercise is too easy
        if last_exercise.is_too_easy():
            return True, last_exercise.time

        # 3. Otherwise, get the most recent sequence of corrects
        most_recent_corrects = []

        for exercise in sorted_exercise_log:
            if exercise.is_correct():
                most_recent_corrects.append(exercise)
            else:
                break

        distinct_days = set()
        for exercise in most_recent_corrects:
            distinct_days.add(exercise.time.date())

        # 4. True: if sufficient corrects in distinct days
        if len(distinct_days) >= CORRECTS_IN_DISTINCT_DAYS_FOR_LEARNED:
            return True, last_exercise.time

        return False, None

    def update_learned_status(self, session):
        """
            To call when something happened to the bookmark,
             that requires it's "learned" status to be updated.
        :param session:
        :return:
        """
        is_learned, learned_time = self.is_learned_based_on_exercise_outcomes()
        log = self.sorted_exercise_log()
        exercise_log_summary = ' '.join([exercise.short_string_summary() for exercise in log])
        if is_learned:
            zeeguu_core.log(f"Log: {exercise_log_summary}: bookmark {self.id} learned!")
            self.learned_time = learned_time
            self.learned = True
            session.add(self)
        else:
            zeeguu_core.log(f"Log: {exercise_log_summary}: bookmark {self.id} not learned yet.")

    def events_indicate_its_learned(self):
        from zeeguu_core.model.smartwatch.watch_interaction_event import \
            WatchInteractionEvent
        events_for_self = WatchInteractionEvent.events_for_bookmark(self)

        for event in events_for_self:
            if event.is_learned_event():
                return True, event.time

        return False, None

    def has_been_learned(self):
        # TODO: This must be stored in the DB together with the
        # bookmark... once a bookmark has been learned, we should
        # not not need to doubt it ... we might still want to confirm
        # say one month later, or three months later...

        """
        :param also_return_time: should the function return also the time when
        the bookmark has been learned?

        :return: boolean indicating whether the bookmark has already been learned,
        togetgher with the time when it was learned if also_return_time is set
        """

        # The first case is when we have an exercise outcome set to Too EASY
        learned, time = self.is_learned_based_on_exercise_outcomes()
        if learned:
            return True, time

        # The second case is when we have an event in the smartwatch event log
        # that indicates that the word has been learned
        learned, time = self.events_indicate_its_learned()
        if learned:
            return learned, time

        return False, None
