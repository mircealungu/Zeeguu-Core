from unittest import TestCase

from tests_zeeguu.model_test_mixin import ModelTestMixIn
from tests_zeeguu.rules.language_rule import LanguageRule
from zeeguu.difficulty_estimation.difficulty_estimator_factory import DifficultyEstimatorFactory
from zeeguu.difficulty_estimation.strategies.default_difficulty_estimator import DefaultDifficultyEstimator
from zeeguu.difficulty_estimation.strategies.flesch_kincaid_difficulty_estimator import \
    FleschKincaidDifficultyEstimator
from zeeguu.difficulty_estimation.strategies.frequency_difficulty_estimator import FrequencyDifficultyEstimator


class DifficultyEstimatorFactoryTest(ModelTestMixIn, TestCase):

    def setUp(self):
        super(DifficultyEstimatorFactoryTest, self).setUp()
        self.en = LanguageRule().en

    def test_ignore_capitalization(self):
        estimator_name = "FKINDEX"
        returned_estimator = DifficultyEstimatorFactory.get_difficulty_estimator(estimator_name, self.en)
        self.assertIsInstance(returned_estimator, FleschKincaidDifficultyEstimator)

    def test_unknown_type_returns_default(self):
        unknown_type = "unknown_type"
        returned_estimator = DifficultyEstimatorFactory.get_difficulty_estimator(unknown_type, self.en)
        self.assertIsInstance(returned_estimator, DefaultDifficultyEstimator)

    def test_returns_frequency_count_estimator(self):
        estimator_name = "FrequencyDifficultyEstimator"
        returned_estimator = DifficultyEstimatorFactory.get_difficulty_estimator(estimator_name, self.en)
        self.assertIsInstance(returned_estimator, FrequencyDifficultyEstimator)

    def test_returns_flesch_kincaid_estimator(self):
        estimator_name = "FleschKincaidDifficultyEstimator"
        returned_estimator = DifficultyEstimatorFactory.get_difficulty_estimator(estimator_name, self.en)
        self.assertIsInstance(returned_estimator, FleschKincaidDifficultyEstimator)

    def test_custom_names_flesch_kincaid_estimator(self):
        custom_names = ["FKIndex", "fk", "flesch-kincaid"]
        for name in custom_names:
            returned_estimator = DifficultyEstimatorFactory.get_difficulty_estimator(name, self.en)
            self.assertIsInstance(returned_estimator, FleschKincaidDifficultyEstimator)
