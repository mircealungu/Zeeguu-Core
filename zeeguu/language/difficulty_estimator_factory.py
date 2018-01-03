from zeeguu.language.strategies.default_difficulty_estimator import DefaultDifficultyEstimator
from zeeguu.language.strategies.frequency_difficulty_estimator import FrequencyDifficultyEstimator


class DifficultyEstimatorFactory:

    # Todo: Discover Difficulty Estimators
    _difficulty_estimators = [FrequencyDifficultyEstimator]
    _default_estimator = DefaultDifficultyEstimator

    @classmethod
    def get_difficulty_estimator(cls, type):
        """
        Returns the difficulty estimator based on the given type name
        :param type:
        :return:
        """
        for estimator in cls._difficulty_estimators:
            if estimator.is_type(type):
                return estimator

        return cls._default_estimator # return default estimator
