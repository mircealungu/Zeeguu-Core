#
import datetime
import json
import random
import re

import sqlalchemy.orm
import zeeguu_core
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound
from zeeguu_core import util
from zeeguu_core.language.difficulty_estimator_factory import DifficultyEstimatorFactory
from zeeguu_core.model.language import Language
from wordstats import Word

db = zeeguu_core.db


class User(db.Model):
    __table_args__ = {'mysql_collate': 'utf8_bin'}

    EMAIL_VALIDATION_REGEX = r"(^[a-z0-9_.+-]+@[a-z0-9-]+\.[a-z0-9-.]+$)"
    ANONYMOUS_EMAIL_DOMAIN = '@anon.zeeguu'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    name = db.Column(db.String(255))
    invitation_code = db.Column(db.String(255))
    password = db.Column(db.String(255))
    password_salt = db.Column(db.String(255))
    learned_language_id = db.Column(
        db.Integer,
        db.ForeignKey(Language.id)
    )
    learned_language = relationship(Language, foreign_keys=[learned_language_id])

    native_language_id = db.Column(
        db.Integer,
        db.ForeignKey(Language.id)
    )
    native_language = relationship(Language, foreign_keys=[native_language_id])

    from zeeguu_core.model.cohort import Cohort
    cohort_id = Column(Integer, ForeignKey(Cohort.id))
    cohort = relationship(Cohort)

    def __init__(self, email, name, password, learned_language=None, native_language=None, invitation_code=None,
                 cohort=None):
        self.email = email
        self.name = name
        self.update_password(password)
        self.learned_language = learned_language or Language.default_learned()
        self.native_language = native_language or Language.default_native_language()
        self.invitation_code = invitation_code
        self.cohort = cohort

    @classmethod
    def create_anonymous(cls, uuid, password, learned_language_code=None, native_language_code=None):
        """

        :param uuid:
        :param password:
        :param learned_language_code:
        :param native_language_code:
        :return:
        """

        # since the DB must have an email we generate a fake one
        fake_email = uuid + cls.ANONYMOUS_EMAIL_DOMAIN

        if learned_language_code is not None:
            try:
                learned_language = Language.find_or_create(learned_language_code)
            except NoResultFound as e:
                learned_language = None
        else:
            learned_language = None

        if native_language_code is not None:
            try:
                native_language = Language.find_or_create(native_language_code)
            except NoResultFound as e:
                native_language = None
        else:
            native_language = None

        new_user = cls(fake_email, uuid, password, learned_language=learned_language, native_language=native_language)

        return new_user

    def __repr__(self):
        return '<User %r>' % (self.email)

    def details_as_dictionary(self):
        from zeeguu_core.model import UserLanguage

        result = dict(
            email=self.email,
            name=self.name,
            learned_language=self.learned_language.code,
            native_language=self.native_language.code
        )

        for each in UserLanguage.query.filter_by(user=self):
            result[each.language.code + "_min"] = each.declared_level_min
            result[each.language.code + "_max"] = each.declared_level_max
            result[each.language.code + "_reading"] = each.reading_news
            result[each.language.code + "_exercises"] = each.doing_exercises

        return result

    def preferred_difficulty_estimator(self):
        """
        :return: Difficulty estimator from preferences,
        otherwise the default one which is FrequencyDifficultyEstimator
        """

        from zeeguu_core.model.user_preference import UserPreference
        # Must have this import here to avoid circular dependency

        preference = UserPreference.get_difficulty_estimator(self) or "FleschKincaidDifficultyEstimator"
        zeeguu_core.log(f"Difficulty estimator for user {self.id}: {preference}")
        return preference

    def text_difficulty(self, text, language):

        estimator = DifficultyEstimatorFactory.get_difficulty_estimator(self.preferred_difficulty_estimator())
        return estimator.estimate_difficulty(text, language, self)

    def set_learned_language(self, code, session = None):
        self.learned_language = Language.find(code)
        from zeeguu_core.model import UserLanguage
        language = UserLanguage(self, self.learned_language, reading_news=True)
        if session:
            session.add(language)

    def set_native_language(self, code):
        self.native_language = Language.find(code)

    def has_bookmarks(self):
        return self.bookmark_count() > 0

    def date_of_last_bookmark(self):
        """
            assumes that there are bookmarks
        """
        return self.bookmarks_chronologically()[0].time

    def active_during_recent(self, days: int = 30):
        if not self.has_bookmarks():
            return False

        import dateutil.relativedelta
        now = datetime.datetime.now()
        a_while_ago = now - dateutil.relativedelta.relativedelta(days=days)
        return self.date_of_last_bookmark() > a_while_ago

    @classmethod
    @sqlalchemy.orm.validates("email")
    def validate_email(cls, col, email):
        if (any(x.isupper() for x in email)):
            raise ValueError("You should use only lowercase letters for email")
        if not re.match(cls.EMAIL_VALIDATION_REGEX, email):
            raise ValueError("Invalid email address")
        return email

    @classmethod
    @sqlalchemy.orm.validates("password")
    def validate_password(cls, col, password):
        if password is None or len(password) == 0:
            raise ValueError("Invalid password")
        return password

    @classmethod
    @sqlalchemy.orm.validates("name")
    def validate_name(cls, col, name):
        if name is None or len(name) == 0:
            raise ValueError("Invalid username")
        return name

    def update_password(self, password: str):
        """
        
        :param password: str
        :return: 
        """
        salt_bytes = "".join(chr(random.randint(0, 255)) for _ in range(32)).encode('utf-8')

        self.password = util.password_hash(password, salt_bytes)
        self.password_salt = salt_bytes.hex()

    def all_reading_sessions(self, after_date=datetime.datetime(1970, 1, 1),
                             before_date=datetime.date.today() + datetime.timedelta(
                                 days=1)):
        from zeeguu_core.model.user_reading_session import UserReadingSession
        return UserReadingSession.query. \
            filter_by(user_id=self.id). \
            filter(UserReadingSession.start_time >= after_date). \
            filter(UserReadingSession.start_time <= before_date). \
            order_by(UserReadingSession.start_time).all()

    def all_bookmarks(self, after_date=datetime.datetime(1970, 1, 1),
                      before_date=datetime.date.today() + datetime.timedelta(
                          days=1)):
        from zeeguu_core.model.bookmark import Bookmark
        return Bookmark.query. \
            filter_by(user_id=self.id). \
            filter(Bookmark.time >= after_date). \
            filter(Bookmark.time <= before_date). \
            order_by(Bookmark.time).all()

    def all_bookmarks_fit_for_study(self):
        from zeeguu_core.model.bookmark import Bookmark
        return Bookmark.query. \
            filter_by(user_id=self.id). \
            filter_by(fit_for_study=True).all()

    def bookmarks_chronologically(self):
        from zeeguu_core.model.bookmark import Bookmark
        return Bookmark.query.filter_by(user_id=self.id).order_by(
            Bookmark.time.desc()).all()

    def starred_bookmarks(self, count):
        from zeeguu_core.model.bookmark import Bookmark
        return Bookmark.query.filter_by(user_id=self.id).filter_by(starred=True).order_by(
            Bookmark.time.desc()).limit(count)

    def learned_bookmarks(self, count=50):
        from zeeguu_core.model.bookmark import Bookmark

        learned = Bookmark.query.filter_by(user_id=self.id).filter_by(learned=True).order_by(
            Bookmark.learned_time.desc()).limit(400)

        return learned

    def top_bookmarks(self, count=50, also_print=False):
        from zeeguu_core.model.bookmark import Bookmark

        def rank(b):
            return Word.stats(b.origin.word, b.origin.language.code).rank

        all_bookmarks = Bookmark.query.filter_by(user_id=self.id).filter_by(learned=False).order_by(
            Bookmark.time.desc()).limit(400)

        single_word_bookmarks = [each for each in all_bookmarks if each.quality_top_bookmark()]

        sorted_bookmarks = sorted(single_word_bookmarks,
                                  key=lambda b: rank(b))
        sorted_bookmarks = sorted_bookmarks[:count]

        if also_print:
            for b in sorted_bookmarks:
                print(f"{b.origin.word} ({b.origin.language.code})- {rank(b)} (id: {b.id})")

        return sorted_bookmarks

    def _datetime_to_date(self, date_time):
        """
            we define datetime as being any datetime object,
            and date as being a datetime object with only the year, month and day part
        """
        return date_time.replace(date_time.year,
                                 date_time.month,
                                 date_time.day, 0, 0, 0,
                                 0)

    def _to_date_dict(self, dict_list, date_key):
        """
            :param dict_list: a list of dictionaries 
            :param date_key: the key that maps to the datetime object in the dictionary 
            :return: dictionary with dates mapping to a list of dictionaries
        """
        date_dict = dict()
        for dictionary in dict_list:
            date = self._datetime_to_date(getattr(dictionary, date_key))
            date_dict.setdefault(date, []).append(dictionary)

        return date_dict

    def _to_serializable(self, tuple_list, key_name, *args):
        """
            :param tuple_list: a list of tuples with 
                1. position: date  
                2. position: list of objects with 'json_serializable_dict()' method
            :param key_name: the key name of the final serialized objects in the result list
            :param *args: the list of arguments that should be passed down to the 'json_serializable_dict()' method
            :return:
        """
        result = []

        for date, object_list in tuple_list:
            serialized_objects = []
            for obj in object_list:
                serialized_objects.append(obj.json_serializable_dict(*args))
            date_entry = dict(
                date=date.strftime("%A, %d %B %Y"),
            )
            date_entry[key_name] = serialized_objects
            result.append(date_entry)

        return result

    def reading_sessions_by_day(self,
                                after_date=datetime.datetime(2010, 1, 1), max=42):
        """
        :param after_date: The date from which the reading sessions will be queried
        :return: a serializable list of of objects containing a date and all the reading sessions belonging to that date
        """

        reading_sessions = self.all_reading_sessions(after_date)
        date_reading_sessions_dict = self._to_date_dict(dict_list=reading_sessions, date_key='start_time')
        sorted_date_reading_sessions_tuples = sorted(date_reading_sessions_dict.items(), reverse=True,
                                                     key=lambda tup: tup[0])

        if (len(sorted_date_reading_sessions_tuples) > max):
            sorted_date_reading_sessions_tuples = sorted_date_reading_sessions_tuples[:max]

        result = self._to_serializable(sorted_date_reading_sessions_tuples, key_name='reading_sessions')

        return result

    def bookmarks_by_date(self, after_date=datetime.datetime(1970, 1, 1)):
        """
        :param after_date:
        :return: a pair of 1. a dict with date-> bookmarks and 2. a sorted list of dates
        """

        def extract_day_from_date(bookmark):
            return bookmark, bookmark.time.replace(bookmark.time.year,
                                                   bookmark.time.month,
                                                   bookmark.time.day, 0, 0, 0,
                                                   0)

        bookmarks = self.all_bookmarks(after_date)
        bookmarks_by_date = dict()

        for elem in map(extract_day_from_date, bookmarks):
            bookmarks_by_date.setdefault(elem[1], []).append(elem[0])

        sorted_dates = list(bookmarks_by_date.keys())
        sorted_dates.sort(reverse=True)
        return bookmarks_by_date, sorted_dates

    def bookmarks_by_day(self, with_context,
                         after_date=datetime.datetime(2010, 1, 1), max=42, with_title=False):

        bookmarks = self.all_bookmarks(after_date)
        date_bookmarks_dict = self._to_date_dict(dict_list=bookmarks, date_key='time')
        sorted_date_bookmarks = sorted(date_bookmarks_dict.items(), reverse=True, key=lambda tup: tup[0])

        if (len(sorted_date_bookmarks) > max):
            sorted_date_bookmarks = sorted_date_bookmarks[:max]

        result = self._to_serializable(sorted_date_bookmarks, 'bookmarks', with_context, with_title)
        return result

    def bookmarks_for_article(self, article_id, with_context, with_title=False):

        from zeeguu_core.model import Bookmark, Text

        bookmarks = []

        all_for_article = (Bookmark.query.join(Text).
                           filter(Bookmark.user_id == self.id).
                           filter(Text.article_id == article_id).
                           order_by(Bookmark.id.asc()).
                           all())

        for each in all_for_article:
            bookmarks.append(each.json_serializable_dict(with_context, with_title))

        return bookmarks

    def bookmarks_by_url_by_date(self, n_days=365):
        bookmarks_list, dates = self.bookmarks_by_date()

        most_recent_n_days = dates[0:n_days]

        urls_by_date = {}
        texts_by_url = {}
        for date in most_recent_n_days:
            for bookmark in bookmarks_list[date]:
                urls_by_date.setdefault(date, set()).add(bookmark.text.url)
                texts_by_url.setdefault(bookmark.text.url, set()).add(bookmark.text)
        return most_recent_n_days, urls_by_date, texts_by_url

    def bookmarks_to_study(self, bookmark_count=10):
        """

        :param bookmark_count: by default we recommend 10 words

        :return:
        """
        from zeeguu_core.word_scheduling import arts

        bookmarks = arts.bookmarks_to_study(self, bookmark_count, zeeguu_core.db)

        return bookmarks

    def bookmark_counts_by_date(self):
        """returns array with added bookmark amount per each date for the last year
        this function is for the activity_graph, generates data
        """

        # compute bookmark_counts_by_date
        year = datetime.date.today().year - 1  # get data from year 2015(if this year is 2016)
        month = datetime.date.today().month
        bookmarks_dict, dates = self.bookmarks_by_date(
            datetime.datetime(year, month, 1))

        counts = []
        for date in dates:
            the_date = date.strftime('%Y-%m-%d')
            the_count = len(bookmarks_dict[date])
            counts.append(dict(date=the_date, count=the_count))

        bookmark_counts_by_date = json.dumps(counts)
        return bookmark_counts_by_date

    def learner_stats_data(self):
        """returns array with learned and learning words count per each month for the last year
        this function is for the line_graph, generates data
        """

        # compute learner_stats_data
        from zeeguu_core.model.learner_stats.learner_stats import \
            compute_learner_stats
        learner_stats_data = compute_learner_stats(self)

        return learner_stats_data

    def user_words(self):
        return [b.origin.word for b in self.all_bookmarks()]

    def bookmark_count(self):
        return len(self.all_bookmarks())

    def word_count(self):
        return len(self.user_words())

    def levels_for(self, language: Language):
        """

            the level that the system considers for this user

            TODO: must think better about this...

        :param language:

        :return: pair of level_min and level_max for this user

        """
        from zeeguu_core.model import UserLanguage

        lang_info = UserLanguage.with_language_id(language.id, self)

        # default values, for when there's no corresponding setting
        declared_level_min = -1
        declared_level_max = 11

        # start from user's levels if they exist
        if lang_info.declared_level_min:
            declared_level_min = lang_info.declared_level_min

        if lang_info.declared_level_max:
            declared_level_max = lang_info.declared_level_max

        # If there's cohort info, consider it
        if self.cohort:
            if self.cohort.language:
                if self.cohort.language == language:
                    if self.cohort.declared_level_min:
                        # min will be the max between the teacher's min and the student's min
                        # this means that if the teacher says 5 is min, the student can't reduce it...
                        # otoh, if the teacher says 5 is the min but the student wants 7 that will work
                        declared_level_min = max(declared_level_min, self.cohort.declared_level_min)

                    if self.cohort.declared_level_max:
                        # a student is limited to the upper limit of his cohort
                        declared_level_max = min(declared_level_max, self.cohort.declared_level_max)

        return max(declared_level_min, 0), min(declared_level_max, 10)

    @classmethod
    def find_all(cls):
        return User.query.all()

    @classmethod
    def find(cls, email):
        return User.query.filter(User.email == email).one()

    @classmethod
    def find_by_id(cls, id):
        return User.query.filter(User.id == id).one()

    @classmethod
    def all_recent_user_ids(cls, days=90):
        from zeeguu_core.model import UserActivityData
        sometime_ago = datetime.datetime.now() - datetime.timedelta(days=days)
        recent_activities = UserActivityData.query.filter(UserActivityData.time > sometime_ago).all()
        user_ids = set([each.user_id for each in recent_activities])
        return user_ids

    @classmethod
    def exists(cls, user):
        try:
            cls.query.filter_by(
                email=user.email,
                id=user.id
            ).one()
            return True
        except NoResultFound:
            return False

    @classmethod
    def authorize(cls, email, password):
        try:
            user = cls.query.filter(cls.email == email).one()
            if user.password == util.password_hash(password, bytes.fromhex(user.password_salt)):
                return user
        except sqlalchemy.orm.exc.NoResultFound:
            return None

    @classmethod
    def authorize_anonymous(cls, uuid, password):
        email = uuid + cls.ANONYMOUS_EMAIL_DOMAIN
        return cls.authorize(email, password)
