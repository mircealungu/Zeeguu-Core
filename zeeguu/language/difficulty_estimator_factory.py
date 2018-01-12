from typing import Type

from zeeguu.language.difficulty_estimator_strategy import DifficultyEstimatorStrategy
from zeeguu.language.strategies.default_difficulty_estimator import DefaultDifficultyEstimator
from zeeguu.language.strategies.flesch_kincaid_difficulty_estimator import \
    FleschKincaidDifficultyEstimator
from zeeguu.language.strategies.frequency_difficulty_estimator import FrequencyDifficultyEstimator


class DifficultyEstimatorFactory:

    # Todo: Discover Difficulty Estimators
    _difficulty_estimators = {FrequencyDifficultyEstimator, FleschKincaidDifficultyEstimator}
    _default_estimator = DefaultDifficultyEstimator

    @classmethod
    def get_difficulty_estimator(cls, estimator_name: str) -> Type[DifficultyEstimatorStrategy]:
        """
        Returns the difficulty estimator based on the given type name
        :param estimator_name: String value name of the difficulty estimator class
        :return:
        """
        for estimator in cls._difficulty_estimators:
            if estimator.is_type(estimator_name):
                return estimator

        return cls._default_estimator
