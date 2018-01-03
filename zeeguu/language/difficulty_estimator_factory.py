from zeeguu.language.strategies.default_difficulty_estimator import DefaultDifficultyEstimator
from zeeguu.language.strategies.frequency_difficulty_estimator import FrequencyDifficultyEstimator


class DifficultyEstimatorFactory:

    difficulty_estimators = [FrequencyDifficultyEstimator]
    default_estimator = DefaultDifficultyEstimator

    @classmethod
    def get_difficulty_estimator(cls, type):
        for estimator in cls.difficulty_estimators:
            if estimator.is_type(type):
                return estimator

        return cls.default_estimator # Default estimator
