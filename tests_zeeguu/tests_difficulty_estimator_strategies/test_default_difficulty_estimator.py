from unittest import TestCase

from tests_zeeguu.model_test_mixin import ModelTestMixIn
from tests_zeeguu.rules.language_rule import LanguageRule
from tests_zeeguu.rules.user_rule import UserRule
from zeeguu.difficulty_estimation.strategies.default_difficulty_estimator import DefaultDifficultyEstimator

SIMPLE_TEXT = "Das ist "
COMPLEX_TEXT = "Alle hatten in sein Lachen eingestimmt, hauptsächlich aus Ehrerbietung " \
               "gegen das Familienoberhaupt"

class DefaultDifficultyEstimatorTest(ModelTestMixIn, TestCase):

    def setUp(self):
        super().setUp()
        self.lan = LanguageRule().de
        self.user = UserRule().user

    def test_compute_simple_text_difficulty(self):
        d1 = DefaultDifficultyEstimator(self.lan, self.user).estimate_difficulty(SIMPLE_TEXT)

        assert d1['discrete'] == 'EASY'
        assert d1['normalized'] == 0

    def test_compute_complex_text_difficulty(self):
        d1 = DefaultDifficultyEstimator(self.lan, self.user).estimate_difficulty(COMPLEX_TEXT)

        assert d1['discrete'] == 'EASY'
        assert d1['normalized'] == 0