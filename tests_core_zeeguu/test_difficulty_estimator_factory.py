from unittest import TestCase

from tests_core_zeeguu.model_test_mixin import ModelTestMixIn
from zeeguu.language.difficulty_estimator_factory import DifficultyEstimatorFactory
from zeeguu.language.strategies.default_difficulty_estimator import DefaultDifficultyEstimator
from zeeguu.language.strategies.flesch_kincaid_reading_ease_difficulty_estimator import \
    FleschKincaidReadingEaseDifficultyEstimator
from zeeguu.language.strategies.frequency_difficulty_estimator import FrequencyDifficultyEstimator


class DifficultyEstimatorFactoryTest(ModelTestMixIn, TestCase):


    def test_unknown_type_returns_default(self):
        unknown_type = "unkown_type"
        returned_estimator = DifficultyEstimatorFactory.get_difficulty_estimator(unknown_type)
        self.assertEqual(returned_estimator, DefaultDifficultyEstimator)


    def test_returns_frequency_count_estimator(self):
        estimator_name = "FrequencyDifficultyEstimator"
        returned_estimator = DifficultyEstimatorFactory.get_difficulty_estimator(estimator_name)
        self.assertEqual(returned_estimator, FrequencyDifficultyEstimator)

    def test_returns_flesch_kincaid_reading_ease_estimator(self):
        estimator_name = "FleschKincaidReadingEaseDifficultyEstimator"
        returned_estimator = DifficultyEstimatorFactory.get_difficulty_estimator(estimator_name)
        self.assertEqual(returned_estimator, FleschKincaidReadingEaseDifficultyEstimator)
