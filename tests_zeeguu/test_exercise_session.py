from unittest import TestCase
from tests_zeeguu.model_test_mixin import ModelTestMixIn
import zeeguu
from tests_zeeguu.rules.user_exercise_session_rule import ExerciseSessionRule
from tests_zeeguu.rules.user_rule import UserRule
from zeeguu.model.user_exercise_session import UserExerciseSession
from zeeguu.model.exercise import Exercise
from zeeguu.model.bookmark import bookmark_exercise_mapping, Bookmark
from datetime import datetime, timedelta

db_session = zeeguu.db.session


class UserExerciseSessionTest(ModelTestMixIn, TestCase):

    def setUp(self):
        super().setUp()
        exercise_session_rule = ExerciseSessionRule()
        self.ex_session1 = exercise_session_rule.exercise_session
        self.user = exercise_session_rule.user
        self.bookmark = exercise_session_rule.bookmark
        self.exercises = Exercise.find(user_id=self.user.id)
        
        self.exercise_session_timeout = UserExerciseSession.get_exercise_session_timeout()
        self.VERY_FAR_IN_THE_PAST = '2000-01-01T00:00:00'
        self.VERY_FAR_IN_THE_FUTURE = '2030-01-01T00:00:00'
        self.TIMEOUT_MINUTES_IN_THE_PAST = datetime.now() - timedelta(minutes=self.exercise_session_timeout)
        self.TWICE_TIMEOUT_MINUTES_IN_THE_PAST = datetime.now() - timedelta(minutes=self.exercise_session_timeout * 2)

    # One result scenario
    def test__get_exercise_session1(self):
        #Since the ex_session1 rule saves the exercise_session in the DB, we expect to find it there
        assert UserExerciseSession._find_most_recent_session(self.ex_session1.user_id, db_session)

    # Many results scenario
    def test__get_exercise_session2(self):
        self.ex_session2 = ExerciseSessionRule().exercise_session
        self.ex_session2.user_id = self.ex_session1.user_id
        resulting_exercise_session = UserExerciseSession._find_most_recent_session(self.ex_session1.user_id, db_session)
        assert resulting_exercise_session.is_active

    def test__is_same_exercise_session(self):
        self.ex_session1.last_action_time = self.TIMEOUT_MINUTES_IN_THE_PAST
        assert (True == self.ex_session1._is_still_active())

    def test__is_not_same_exercise_session(self):
        new_exercise_session = UserExerciseSession(self.ex_session1.user_id)
        new_exercise_session.last_action_time = self.TWICE_TIMEOUT_MINUTES_IN_THE_PAST
        assert (False == new_exercise_session._is_still_active())

    def test__update_last_use(self):
        current_time = datetime.now()
        updated_session = self.ex_session1._update_last_action_time(db_session, current_time)
        assert (current_time  == updated_session.last_action_time)

    # Closing a session returns it in case everything went well
    def test__close_session(self):
        assert self.ex_session1 == self.ex_session1._close_exercise_session(db_session)

    # Scenario 1 = There is an active and still valid session
    def test__update_exercise_session_scenario1(self):
        self.ex_session1.last_action_time = self.TIMEOUT_MINUTES_IN_THE_PAST
        self.exercises[0].time = datetime.now()
        updated_session = UserExerciseSession.update_exercise_session(self.exercises[0], db_session)
        assert updated_session == self.ex_session1

    # Scenario2 = There is an active but no longer valid session
    def test__update_exercise_session_scenario2(self):
        self.ex_session1.last_action_time = self.TWICE_TIMEOUT_MINUTES_IN_THE_PAST
        self.exercises[0].time = datetime.now()
        resulting_exercise_session = UserExerciseSession.update_exercise_session(self.exercises[0], db_session)
        assert resulting_exercise_session != self.ex_session1

    # Scenario 3: There is no active session for the user
    def test__update_exercise_session_scenario3(self):
        self.ex_session1.is_active = False
        resulting_exercise_session = UserExerciseSession.update_exercise_session(self.exercises[0], db_session)
        assert resulting_exercise_session != self.ex_session1

    #Scenario 4: There are some cases of exercises not associated to a bookmark, therefore we obtain None
    def test__update_exercise_session_scenario4(self):
        #Delete all the bookmark records so that the exercise has no mapping to any
        Bookmark.query.delete()
        db_session.commit()
        resulting_exercise_session = UserExerciseSession.update_exercise_session(self.exercises[0], db_session)
        assert (None == resulting_exercise_session)

    def test__find_by_user_only_one_active(self):
        user = self.ex_session1.user
        active_sessions = UserExerciseSession.find_by_user(user.id, self.VERY_FAR_IN_THE_PAST, self.VERY_FAR_IN_THE_FUTURE,
                                                           is_active=True)
        assert len(active_sessions) == 1

    def test__find_by_user_two_inactive(self):
        # WHEN: we have two sessions, and both are not active
        user = self.ex_session1.user

        self.ex_session1.is_active = False

        self.ex_session2 = ExerciseSessionRule().exercise_session
        self.ex_session2.user_id = user.id
        self.ex_session2.is_active = False

        # THEN: we find both of them
        all_sessions = UserExerciseSession.find_by_user(user.id, self.VERY_FAR_IN_THE_PAST, self.VERY_FAR_IN_THE_FUTURE)
        assert len(all_sessions) == 2

    def test__find_by_cohort(self):
        cohort_id = self.ex_session1.user.cohort_id
        active_sessions = UserExerciseSession.find_by_cohort(cohort_id, self.VERY_FAR_IN_THE_PAST, self.VERY_FAR_IN_THE_FUTURE,
                                                             is_active=True)
        assert active_sessions
