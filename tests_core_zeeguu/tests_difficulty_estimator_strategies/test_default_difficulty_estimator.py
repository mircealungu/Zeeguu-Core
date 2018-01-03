from unittest import TestCase

from tests_core_zeeguu.model_test_mixin import ModelTestMixIn
from tests_core_zeeguu.rules.language_rule import LanguageRule
from zeeguu.language.strategies.default_difficulty_estimator import DefaultDifficultyEstimator

SIMPLE_TEXT = "Das ist "
COMPLEX_TEXT = "Alle hatten in sein Lachen eingestimmt, hauptsächlich aus Ehrerbietung " \
               "gegen das Familienoberhaupt"

class DefaultDifficultyEstimatorTest(ModelTestMixIn, TestCase):

    def setUp(self):
        super().setUp()
        self.lan = LanguageRule().de

    def test_compute_simple_text_difficulty(self):
        d1 = DefaultDifficultyEstimator.estimate_difficulty(SIMPLE_TEXT, self.lan)

        assert d1['estimated_difficulty'] == 'EASY'
        assert d1['score_average'] == 0
        assert d1['score_median'] == 0

    def test_compute_complex_text_difficulty(self):
        d1 = DefaultDifficultyEstimator.estimate_difficulty(COMPLEX_TEXT, self.lan)

        assert d1['estimated_difficulty'] == 'EASY'
        assert d1['score_average'] == 0
        assert d1['score_median'] == 0