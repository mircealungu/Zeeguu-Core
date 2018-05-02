from unittest import TestCase
from tests_zeeguu.model_test_mixin import ModelTestMixIn
import zeeguu
from tests_zeeguu.rules.user_working_session_rule import WorkingSessionRule
from zeeguu.model.user_working_session import UserWorkingSession
from datetime import datetime, timedelta

db_session = zeeguu.db.session


class UserWorkingSessionTest(ModelTestMixIn, TestCase):

    def setUp(self):
        super().setUp()
        self.session_rule = WorkingSessionRule().w_session
        self.working_session_timeout = UserWorkingSession.get_working_session_timeout()

    # One result scenario
    def test_get_working_session1(self):
        assert UserWorkingSession._find(self.session_rule.user_id, self.session_rule.article_id, db_session)

    # Many results scenario
    def test_get_working_session2(self):
        self.session_rule2 = WorkingSessionRule().w_session
        self.session_rule2.user_id = self.session_rule.user_id
        self.session_rule2.article_id = self.session_rule.article_id
        assert UserWorkingSession._find(self.session_rule.user_id, self.session_rule.article_id, db_session)
        
    def test_is_same_working_session(self):
        self.session_rule.last_action_time = datetime.now() - timedelta(minutes=self.working_session_timeout)
        assert (True == self.session_rule._is_same_working_session())

    def test_is_not_same_working_session(self):
        self.session_rule.last_action_time = datetime.now() - timedelta(minutes=self.working_session_timeout * 2)
        assert (False == self.session_rule._is_same_working_session())

    # One result scenario (add grace time)
    def test__update_last_use1(self):
        assert self.session_rule._update_last_use(db_session, add_grace_time=True)

    # One result scenario (no grace time)
    def test__update_last_use2(self):
        assert self.session_rule._update_last_use(db_session, add_grace_time=False)

    # Many results scenario
    def test__update_last_use3(self):
        self.session_rule2 = WorkingSessionRule().w_session
        self.session_rule2.user_id = self.session_rule.user_id
        self.session_rule2.article_id = self.session_rule.article_id
        assert self.session_rule._update_last_use(db_session, add_grace_time=True)

    def test__close_session(self):
        assert self.session_rule._close_working_session(db_session)

    def test__close_user_sessions(self):
        assert (None == UserWorkingSession._close_user_working_sessions(db_session, self.session_rule.user_id))

    # Open action / different session
    def test_update_working_session_scenario1(self):
        event = "UMR - OPEN ARTICLE"
        self.session_rule.is_active = False
        assert UserWorkingSession.update_working_session(db_session, 
                                                            event, 
                                                            self.session_rule.user_id, 
                                                            self.session_rule.article_id
                                                        )

    # Open action / open and same session
    def test_update_working_session_scenario2(self):
        event = "UMR - OPEN ARTICLE"
        assert UserWorkingSession.update_working_session(db_session, 
                                                            event, 
                                                            self.session_rule.user_id, 
                                                            self.session_rule.article_id
                                                        )

    # Open action / open but different/older session
    def test_update_working_session_scenario3(self):
        event = "UMR - OPEN ARTICLE"
        self.session_rule.last_action_time = datetime.now() - timedelta(minutes=self.working_session_timeout * 2)
        assert UserWorkingSession.update_working_session(db_session, 
                                                            event, 
                                                            self.session_rule.user_id, 
                                                            self.session_rule.article_id
                                                        )

    # Closing action / active and same working session
    def test_update_working_session_scenario4(self):
        event = "UMR - ARTICLE CLOSED"
        assert UserWorkingSession.update_working_session(db_session, 
                                                            event, 
                                                            self.session_rule.user_id, 
                                                            self.session_rule.article_id
                                                        )

    # Closing action / active but different working session
    def test_update_working_session_scenario5(self):
        event = "UMR - ARTICLE CLOSED"
        self.session_rule.last_action_time = datetime.now() - timedelta(minutes=self.working_session_timeout * 2)
        assert UserWorkingSession.update_working_session(db_session, 
                                                            event, 
                                                            self.session_rule.user_id, 
                                                            self.session_rule.article_id
                                                        )

    def test_find_by_user(self):
        user = self.session_rule.user
        active_sessions = self.session_rule.find_by_user(user.id, '2000-01-01T00:00:00', '2020-01-01T00:00:00', True)
        assert active_sessions

    def test_find_by_cohort(self):
        cohort_id = self.session_rule.user.cohort_id
        active_sessions = self.session_rule.find_by_cohort(cohort_id, '2000-01-01T00:00:00', '2020-01-01T00:00:00',
                                                           True)
        assert active_sessions

    # Cohort_id provided
    def test_find_by_article_scenario1(self):
        article_id = self.session_rule.article_id
        cohort_id = self.session_rule.user.cohort_id
        active_sessions = self.session_rule.find_by_article(article_id, '2000-01-01T00:00:00', '2020-01-01T00:00:00',
                                                            True, cohort_id)
        assert active_sessions

    # Empty cohort_id
    def test_find_by_article_scenario2(self):
        article_id = self.session_rule.article_id
        active_sessions = self.session_rule.find_by_article(article_id, '2000-01-01T00:00:00', '2020-01-01T00:00:00',
                                                            True)
        assert active_sessions

    def test_find_by_user_and_article(self):
        user_id = self.session_rule.user_id
        article_id = self.session_rule.article_id
        active_sessions = self.session_rule.find_by_user_and_article(user_id, article_id)
        assert active_sessions