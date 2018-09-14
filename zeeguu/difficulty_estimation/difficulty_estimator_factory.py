from typing import Type

from zeeguu.difficulty_estimation.difficulty_estimator_strategy import DifficultyEstimatorStrategy
from zeeguu.difficulty_estimation.strategies.default_difficulty_estimator import DefaultDifficultyEstimator
from zeeguu.difficulty_estimation.strategies.flesch_kincaid_difficulty_estimator import FleschKincaidDifficultyEstimator
from zeeguu.difficulty_estimation.strategies.frequency_difficulty_estimator import FrequencyDifficultyEstimator


class DifficultyEstimatorFactory:

    # Todo: Discover Difficulty Estimators
    _difficulty_estimators = {FrequencyDifficultyEstimator, FleschKincaidDifficultyEstimator}
    _default_estimator = DefaultDifficultyEstimator

    @classmethod
    def get_difficulty_estimator(cls, estimator_name: str, language: 'Language', user:'User' = None) -> Type[DifficultyEstimatorStrategy]:
        """
        Returns the difficulty estimator based on the given estimator name. It first checks if
        there are any estimators with the given class names. When nothing is found it checks the custom
        names of the class.
        :param estimator_name: String value name of the difficulty estimator class
        :return:
        """
        for estimator in cls._difficulty_estimators:
            if estimator.__name__ == estimator_name:
                return estimator(language, user)

        for estimator in cls._difficulty_estimators:
            if estimator.has_custom_name(estimator_name):
                return estimator(language, user)

        return cls._default_estimator(language, user)
