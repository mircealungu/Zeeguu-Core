from unittest import TestCase

from tests_zeeguu.model_test_mixin import ModelTestMixIn
from tests_zeeguu.rules.language_rule import LanguageRule
from tests_zeeguu.rules.user_rule import UserRule
from zeeguu.difficulty_estimation.difficulty_estimator_factory import DifficultyEstimatorFactory
from zeeguu.difficulty_estimation.strategies.default_difficulty_estimator import DefaultDifficultyEstimator
from zeeguu.difficulty_estimation.strategies.frequency_difficulty_estimator import FrequencyDifficultyEstimator

SIMPLE_TEXT = "Das ist mein Leben."
COMPLEX_TEXT = "Alle hatten in sein Lachen eingestimmt, hauptsächlich aus Ehrerbietung " \
               "gegen das Familienoberhaupt"


class FrequencyDifficultyEstimatorTest(ModelTestMixIn, TestCase):

    def setUp(self):
        super().setUp()
        self.lan = LanguageRule().de
        self.user = UserRule().user

    def test_compute_text_difficulty(self):
        estimator = DifficultyEstimatorFactory.get_difficulty_estimator("frequency", self.lan, self.user)

        simple_text_difficulty = estimator.estimate_difficulty(SIMPLE_TEXT)
        complex_text_difficulty = estimator.estimate_difficulty(COMPLEX_TEXT)

        print(simple_text_difficulty)
        print(complex_text_difficulty)

        assert simple_text_difficulty['discrete'] == 'EASY'
        assert complex_text_difficulty['discrete'] == 'HARD'
