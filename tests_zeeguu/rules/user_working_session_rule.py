from datetime import datetime, timedelta
from random import randint
from tests_zeeguu.rules.base_rule import BaseRule
from tests_zeeguu.rules.cohort_rule import CohortRule
from tests_zeeguu.rules.article_rule import ArticleRule
from zeeguu.model.user_working_session import UserWorkingSession



class WorkingSessionRule(BaseRule):
    """

        Creates a Working Session object with random data and saves it to the database.

    """
    def __init__(self):
        super().__init__()

        self.w_session = self._create_model_object()

        self.save(self.w_session)

    def _create_model_object(self):
        cohort = CohortRule()
        user = cohort.student1
        article = ArticleRule().article
        start_time = datetime.now() - timedelta(minutes=randint(0, 7200))

        w_session = UserWorkingSession(user.id, article.id, start_time)

        return w_session
