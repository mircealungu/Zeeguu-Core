from unittest import TestCase
from tests_zeeguu.model_test_mixin import ModelTestMixIn
import zeeguu
from tests_zeeguu.rules.user_reading_session_rule import ReadingSessionRule
from zeeguu.model.user_reading_session import UserReadingSession
from datetime import datetime, timedelta

db_session = zeeguu.db.session


class UserReadingSessionTest(ModelTestMixIn, TestCase):

    def setUp(self):
        super().setUp()
        self.read_session = ReadingSessionRule().w_session
        self.reading_session_timeout = UserReadingSession.get_reading_session_timeout()

    # One result scenario
    def test_get_reading_session1(self):
        #Since the read_session1 rule saves the exercise_session in the DB, we expect to find it there
        assert UserReadingSession._find_active_session(self.read_session.user_id, self.read_session.article_id, db_session)

    # Many results scenario
    def test_get_reading_session2(self):
        self.read_session2 = ReadingSessionRule().w_session
        self.read_session2.user_id = self.read_session.user_id
        self.read_session2.article_id = self.read_session.article_id
        assert UserReadingSession._find_active_session(self.read_session.user_id, self.read_session.article_id, db_session)
        
    def test_is_same_reading_session(self):
        self.read_session.last_action_time = datetime.now() - timedelta(minutes=self.reading_session_timeout)
        assert (True == self.read_session._is_still_active())

    def test_is_not_same_reading_session(self):
        self.read_session.last_action_time = datetime.now() - timedelta(minutes=self.reading_session_timeout * 2)
        assert (False == self.read_session._is_still_active())

    # One result scenario (add grace time)
    def test__update_last_use1(self):
        assert self.read_session == self.read_session._update_last_action_time(db_session, add_grace_time=True)

    # One result scenario (no grace time)
    def test__update_last_use2(self):
        assert self.read_session == self.read_session._update_last_action_time(db_session, add_grace_time=False)

    def test__close_session(self):
        assert self.read_session._close_reading_session(db_session)

    def test__close_user_sessions(self):
        assert (None == UserReadingSession._close_user_reading_sessions(db_session, self.read_session.user_id))

    # Open action / different session
    def test_update_reading_session_scenario1(self):
        event = "UMR - OPEN ARTICLE"
        self.read_session.is_active = False
        assert UserReadingSession.update_reading_session(db_session, 
                                                            event, 
                                                            self.read_session.user_id, 
                                                            self.read_session.article_id
                                                        )

    # Open action / open and same session
    def test_update_reading_session_scenario2(self):
        self.read_session.last_action_time = datetime.now() - timedelta(minutes=self.reading_session_timeout)
        event = "UMR - OPEN ARTICLE"
        assert UserReadingSession.update_reading_session(db_session, 
                                                            event, 
                                                            self.read_session.user_id, 
                                                            self.read_session.article_id
                                                        )

    # Open action / open but different/older session
    def test_update_reading_session_scenario3(self):
        event = "UMR - OPEN ARTICLE"
        self.read_session.last_action_time = datetime.now() - timedelta(minutes=self.reading_session_timeout * 2)
        assert UserReadingSession.update_reading_session(db_session, 
                                                            event, 
                                                            self.read_session.user_id, 
                                                            self.read_session.article_id
                                                        )

    # Closing action / active and same reading session
    def test_update_reading_session_scenario4(self):
        event = "UMR - ARTICLE CLOSED"
        assert UserReadingSession.update_reading_session(db_session, 
                                                            event, 
                                                            self.read_session.user_id, 
                                                            self.read_session.article_id
                                                        )

    # Closing action / active but different reading session
    def test_update_reading_session_scenario5(self):
        event = "UMR - ARTICLE CLOSED"
        self.read_session.last_action_time = datetime.now() - timedelta(minutes=self.reading_session_timeout * 2)
        assert UserReadingSession.update_reading_session(db_session, 
                                                            event, 
                                                            self.read_session.user_id, 
                                                            self.read_session.article_id
                                                        )

    def test_find_by_user(self):
        user = self.read_session.user
        active_sessions = UserReadingSession.find_by_user(user.id, '2000-01-01T00:00:00', '2030-01-01T00:00:00', True)
        assert active_sessions

    def test_find_by_cohort(self):
        cohort_id = self.read_session.user.cohort_id
        active_sessions = UserReadingSession.find_by_cohort(cohort_id, '2000-01-01T00:00:00', '2030-01-01T00:00:00',
                                                           True)
        assert active_sessions

    # Cohort_id provided
    def test_find_by_article_scenario1(self):
        article_id = self.read_session.article_id
        cohort_id = self.read_session.user.cohort_id
        active_sessions = UserReadingSession.find_by_article(article_id, '2000-01-01T00:00:00', '2030-01-01T00:00:00',
                                                            True, cohort_id)
        assert active_sessions

    # Empty cohort_id
    def test_find_by_article_scenario2(self):
        article_id = self.read_session.article_id
        active_sessions = UserReadingSession.find_by_article(article_id, '2000-01-01T00:00:00', '2020-01-01T00:00:00',
                                                            True)
        assert active_sessions

    def test_find_by_user_and_article(self):
        user_id = self.read_session.user_id
        article_id = self.read_session.article_id
        active_sessions = UserReadingSession.find_by_user_and_article(user_id, article_id)
        assert active_sessions