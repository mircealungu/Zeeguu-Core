from unittest import TestCase

from tests_core_zeeguu.rules.user_rule import UserRule

from tests_core_zeeguu.rules.language_rule import LanguageRule

from tests_core_zeeguu.model_test_mixin import ModelTestMixIn
from zeeguu.language.strategies.flesch_kincaid_difficulty_estimator import \
    FleschKincaidDifficultyEstimator

E_EASY_TEXT = "The cat sat on the mat."
E_MEDIUM_TEXT = "This sentence, taken as a reading passage unto itself, is being used to prove a point."
E_HARD_TEXT = "The Australian platypus is seemingly a hybrid of a mammal and reptilian creature."


class FleschKincaidReadingEaseDifficultyEstimatorTest(ModelTestMixIn, TestCase):

    def setUp(self):
        super().setUp()
        self.user = UserRule().user

    # CUSTOM NAMES
    def test_recognized_by_FKIndex(self):
        name = "FKIndex"
        self.assertTrue(FleschKincaidDifficultyEstimator.in_custom_name(name))

    def test_recognized_by_FK(self):
        name = "fk"
        self.assertTrue(FleschKincaidDifficultyEstimator.in_custom_name(name))

    def test_recognized_by_flesch_kincaid(self):
        name = "flesch-kincaid"
        self.assertTrue(FleschKincaidDifficultyEstimator.in_custom_name(name))

    # NORMALIZE TESTS
    def test_normalized_above_100(self):
        d = FleschKincaidDifficultyEstimator.normalize_difficulty(178)
        self.assertEqual(d, 0)

    def test_normalized_100(self):
        d = FleschKincaidDifficultyEstimator.normalize_difficulty(100)
        self.assertEqual(d, 0)

    def test_normalized_between_100_and_0(self):
        d = FleschKincaidDifficultyEstimator.normalize_difficulty(50)
        self.assertEqual(d, 0.5)

    def test_normalized_0(self):
        d = FleschKincaidDifficultyEstimator.normalize_difficulty(0)
        self.assertEqual(d, 1)

    def test_normalized_below_0(self):
        d = FleschKincaidDifficultyEstimator.normalize_difficulty(-10)
        self.assertEqual(d, 1)

    # DISCRETE TESTS
    def test_discrete_above_80(self):
        d = FleschKincaidDifficultyEstimator.discrete_difficulty(100)
        self.assertEqual(d, 'EASY')

    def test_discrete_80(self):
        d = FleschKincaidDifficultyEstimator.discrete_difficulty(80)
        self.assertEqual(d, 'MEDIUM')

    def test_discrete_between_80_and_50(self):
        d = FleschKincaidDifficultyEstimator.discrete_difficulty(60)
        self.assertEqual(d, 'MEDIUM')

    def test_discrete_50(self):
        d = FleschKincaidDifficultyEstimator.discrete_difficulty(50)
        self.assertEqual(d, 'HARD')

    def test_discrete_below_50(self):
        d = FleschKincaidDifficultyEstimator.discrete_difficulty(30)
        self.assertEqual(d, 'HARD')

    def test_discrete_below_0(self):
        d = FleschKincaidDifficultyEstimator.discrete_difficulty(-10)
        self.assertEqual(d, 'HARD')

    # ENGLISH TESTS
    def test_english_easy(self):
        lan = LanguageRule().en
        d = FleschKincaidDifficultyEstimator.estimate_difficulty(E_EASY_TEXT, lan, self.user)

        self.assertEqual(d['discrete'], 'EASY')

    def test_english_medium(self):
        lan = LanguageRule().en
        d = FleschKincaidDifficultyEstimator.estimate_difficulty(E_MEDIUM_TEXT, lan, self.user)

        self.assertEqual(d['discrete'], 'MEDIUM')

    def test_english_hard(self):
        lan = LanguageRule().en
        d = FleschKincaidDifficultyEstimator.estimate_difficulty(E_HARD_TEXT, lan, self.user)

        self.assertEqual(d['discrete'], 'HARD')
