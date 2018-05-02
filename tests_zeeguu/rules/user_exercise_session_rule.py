from datetime import datetime, timedelta
from random import randint
from tests_zeeguu.rules.base_rule import BaseRule
from tests_zeeguu.rules.cohort_rule import CohortRule
from zeeguu.model.user_exercise_session import UserExerciseSession

class ExerciseSessionRule(BaseRule):
    """

        Creates a Exercise Session object with random data and saves it to the database.

    """
    def __init__(self):
        super().__init__()

        self.exercise_session = self._create_model_object()

        self.save(self.exercise_session)

    def _create_model_object(self):
        cohort = CohortRule()
        user = cohort.student1
        start_time = datetime.now() - timedelta(minutes=randint(0, 7200))

        exercise_session = UserExerciseSession(user.id, start_time)

        return exercise_session