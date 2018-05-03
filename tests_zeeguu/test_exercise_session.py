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
        self.ex_session1 = ExerciseSessionRule().exercise_session
        self.exercise_session_timeout = UserExerciseSession.get_exercise_session_timeout()
        self.LONG_TIME_AGO = '2000-01-01T00:00:00'
        self.LONG_TIME_AFTER = '2030-01-01T00:00:00'

    # One result scenario
    def test_get_exercise_session1(self):
        #Since the ex_session1 rule saves the exercise_session in the DB, we expect to find it there
        assert UserExerciseSession._find(self.ex_session1.user_id, db_session)

    # Many results scenario
    def test_get_exercise_session2(self):
        self.ex_session2 = ExerciseSessionRule().exercise_session
        self.ex_session2.user_id = self.ex_session1.user_id
        assert UserExerciseSession._find(self.ex_session1.user_id, db_session)

    def test_is_same_exercise_session(self):
        self.ex_session1.last_action_time = datetime.now() - timedelta(minutes=self.exercise_session_timeout)
        assert (True == self.ex_session1._is_still_active())

    def test_is_not_same_exercise_session(self):
        new_exercise_session = UserExerciseSession(self.ex_session1.user_id)
        new_exercise_session.last_action_time = datetime.now() - timedelta(minutes=self.exercise_session_timeout * 2)
        assert (False == new_exercise_session._is_still_active())

    def test__update_last_use(self):
        assert self.ex_session1._update_last_action_time(db_session)

    # Closing a session returns it in case everything went well
    def test__close_session(self):
        assert self.ex_session1 == self.ex_session1._close_exercise_session(db_session)

    # Scenario 1 = There is an active and still valid session
    def test_update_exercise_session_scenario1(self):
        self.ex_session1.last_action_time = datetime.now() - timedelta(minutes=self.exercise_session_timeout)
        updated_session = UserExerciseSession.update_exercise_session(self.ex_session1.user_id, db_session)
        assert updated_session == self.ex_session1

    # Scenario2 = There is an active but no longer valid session
    def test_update_exercise_session_scenario2(self):
        self.ex_session1.last_action_time = datetime.now() - timedelta(minutes=self.exercise_session_timeout * 2)
        newly_created_session = UserExerciseSession.update_exercise_session(self.ex_session1.user_id, db_session)
        assert newly_created_session != self.ex_session1

    # Scenario 3: There is no active session for the user
    def test_update_exercise_session_scenario3(self):
        self.ex_session1.is_active = False
        newly_created_session = UserExerciseSession.update_exercise_session(self.ex_session1.user_id, db_session)
        assert newly_created_session != self.ex_session1

    def test_find_by_user_only_one_active(self):
        user = self.ex_session1.user
        active_sessions = UserExerciseSession.find_by_user(user.id, self.LONG_TIME_AGO, self.LONG_TIME_AFTER,
                                                           is_active=True)
        assert len(active_sessions) == 1

    def test_find_by_user_two_inactive(self):
        # WHEN: we have two sessions, and both are not active
        user = self.ex_session1.user

        self.ex_session1.is_active = False

        self.ex_session2 = ExerciseSessionRule().exercise_session
        self.ex_session2.user_id = user.id
        self.ex_session2.is_active = False

        # THEN: we find both of them
        all_sessions = UserExerciseSession.find_by_user(user.id, self.LONG_TIME_AGO, self.LONG_TIME_AFTER)
        assert len(all_sessions) == 2

    def test_find_by_cohort(self):
        cohort_id = self.ex_session1.user.cohort_id
        active_sessions = UserExerciseSession.find_by_cohort(cohort_id, self.LONG_TIME_AGO, self.LONG_TIME_AFTER,
                                                             is_active=True)
        assert active_sessions
