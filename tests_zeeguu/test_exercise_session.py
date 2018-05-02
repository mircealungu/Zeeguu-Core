from unittest import TestCase
from tests_zeeguu.model_test_mixin import ModelTestMixIn
import zeeguu
from tests_zeeguu.rules.user_exercise_session_rule import ExerciseSessionRule
from zeeguu.model.user_exercise_session import UserExerciseSession
from datetime import datetime, timedelta

db_session = zeeguu.db.session
class UserExerciseSessionTest(ModelTestMixIn, TestCase):

    def setUp(self):
        super().setUp()
        self.session_rule = ExerciseSessionRule().exercise_session
        self.exercise_session_timeout = UserExerciseSession.get_exercise_session_timeout()

    # One result scenario
    def test_get_exercise_session1(self):
        assert UserExerciseSession._find(self.session_rule.user_id, db_session)

    # Many results scenario
    def test_get_exercise_session2(self):
        self.session_rule2 = ExerciseSessionRule().exercise_session
        self.session_rule2.user_id = self.session_rule.user_id
        assert UserExerciseSession._find(self.session_rule.user_id, db_session)
        
    def test_is_same_exercise_session(self):
        self.session_rule.last_action_time = datetime.now() - timedelta(minutes=self.exercise_session_timeout)
        assert (True == self.session_rule._is_same_exercise_session())

    def test_is_not_same_exercise_session(self):
        new_exercise_session = UserExerciseSession(self.session_rule.user_id)
        new_exercise_session.last_action_time = datetime.now() - timedelta(minutes=self.exercise_session_timeout * 2)
        assert (False == new_exercise_session._is_same_exercise_session())

    # One result scenario
    def test__update_last_use(self):
        assert self.session_rule._update_last_use(db_session)

    # Many results scenario
    def test__update_last_use2(self):
        self.session_rule2 = ExerciseSessionRule().exercise_session
        self.session_rule2.user_id = self.session_rule.user_id
        assert (None == self.session_rule._update_last_use(db_session))

    def test__close_session(self):
        assert self.session_rule._close_exercise_session(db_session)

    # There is an active and still valid session
    def test_update_exercise_session_scenario1(self):
        assert UserExerciseSession.update_exercise_session(self.session_rule.user_id, db_session)

    # There is an active but no longer valid session 
    def test_update_exercise_session_scenario2(self):
        self.session_rule.last_action_time = datetime.now() - timedelta(minutes=self.exercise_session_timeout * 2)
        assert UserExerciseSession.update_exercise_session(self.session_rule.user_id, db_session)

    # There is no active session for the user
    def test_update_exercise_session_scenario3(self):
        self.session_rule.is_active = False
        assert UserExerciseSession.update_exercise_session(self.session_rule.user_id, db_session)

    def test_find_by_user(self):
        user = self.session_rule.user
        active_sessions = self.session_rule.find_by_user(user.id, '2000-01-01T00:00:00', '2020-01-01T00:00:00', True)
        assert active_sessions

    def test_find_by_cohort(self):
        cohort_id = self.session_rule.user.cohort_id
        active_sessions = self.session_rule.find_by_cohort(cohort_id, '2000-01-01T00:00:00', '2020-01-01T00:00:00',
                                                           True)
        assert active_sessions
