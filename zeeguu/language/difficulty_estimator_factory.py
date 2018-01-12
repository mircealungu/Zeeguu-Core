from zeeguu.language.strategies.default_difficulty_estimator import DefaultDifficultyEstimator
from zeeguu.language.strategies.flesch_kincaid_reading_ease_difficulty_estimator import \
    FleschKincaidReadingEaseDifficultyEstimator
from zeeguu.language.strategies.frequency_difficulty_estimator import FrequencyDifficultyEstimator


class DifficultyEstimatorFactory:

    # Todo: Discover Difficulty Estimators
    _difficulty_estimators = [FrequencyDifficultyEstimator, FleschKincaidReadingEaseDifficultyEstimator]
    _default_estimator = DefaultDifficultyEstimator

    @classmethod
    def get_difficulty_estimator(cls, estimator_name : str):
        """
        Returns the difficulty estimator based on the given type name
        :param type: String value name of the difficulty estimator class
        :return:
        """
        for estimator in cls._difficulty_estimators:
            if estimator.is_type(estimator_name):
                return estimator

        return cls._default_estimator
