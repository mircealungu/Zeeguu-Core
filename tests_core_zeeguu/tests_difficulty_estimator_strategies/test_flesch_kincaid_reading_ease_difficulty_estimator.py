from unittest import TestCase

from tests_core_zeeguu.rules.language_rule import LanguageRule

from tests_core_zeeguu.model_test_mixin import ModelTestMixIn
from zeeguu.language.strategies.flesch_kincaid_reading_ease_difficulty_estimator import \
    FleschKincaidReadingEaseDifficultyEstimator

E_EASY_TEXT = "The cat sat on the mat."
E_MEDIUM_TEXT = "This sentence, taken as a reading passage unto itself, is being used to prove a point."
E_HARD_TEXT = "The Australian platypus is seemingly a hybrid of a mammal and reptilian creature."

class FleschKincaidReadingEaseDifficultyEstimatorTest(ModelTestMixIn, TestCase):

    def setUp(self):
        super().setUp()

    ## DISCRETE TESTS
    def test_discrete_above_80(self):
        d = FleschKincaidReadingEaseDifficultyEstimator.discrete_difficulty(100)
        self.assertEqual(d['discrete'], 'EASY')

    def test_discrete_80(self):
        d = FleschKincaidReadingEaseDifficultyEstimator.discrete_difficulty(80)
        self.assertEqual(d['discrete'], 'MEDIUM')

    def test_discrete_between_80_and_50(self):
        d = FleschKincaidReadingEaseDifficultyEstimator.discrete_difficulty(60)
        self.assertEqual(d['discrete'], 'MEDIUM')

    def test_discrete_50(self):
        d = FleschKincaidReadingEaseDifficultyEstimator.discrete_difficulty(50)
        self.assertEqual(d['discrete'], 'HARD')

    def test_below_50(self):
        d = FleschKincaidReadingEaseDifficultyEstimator.discrete_difficulty(30)
        self.assertEqual(d['discrete'], 'HARD')

    def test_below_0(self):
        d = FleschKincaidReadingEaseDifficultyEstimator.discrete_difficulty(-10)
        self.assertEqual(d['discrete'], 'HARD')

    ## ENGLISH TESTS
    def test_english_easy(self):
        lan = LanguageRule().en
        d = FleschKincaidReadingEaseDifficultyEstimator.estimate_difficulty(E_EASY_TEXT, lan)

        self.assertEqual(d['discrete'], 'EASY')

    def test_english_medium(self):
        lan = LanguageRule().en
        d = FleschKincaidReadingEaseDifficultyEstimator.estimate_difficulty(E_MEDIUM_TEXT, lan)

        self.assertEqual(d['discrete'], 'MEDIUM')

    def test_english_hard(self):
        lan = LanguageRule().en
        d = FleschKincaidReadingEaseDifficultyEstimator.estimate_difficulty(E_MEDIUM_TEXT, lan)

        self.assertEqual(d['discrete'], 'HARD')