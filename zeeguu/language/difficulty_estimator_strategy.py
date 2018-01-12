from abc import abstractmethod

from zeeguu import model


class DifficultyEstimatorStrategy:

    CUSTOM_NAMES = []

    @classmethod
    def has_custom_name(cls, estimator_name: str):
        """
        Check if the estimator name is in the custom name list
        :param estimator_name:
        :return:
        """
        in_custom_names = estimator_name.lower() in [name.lower() for name in cls.CUSTOM_NAMES]
        return in_custom_names

    @classmethod
    @abstractmethod
    def estimate_difficulty(cls, text: str, language: 'model.Language', user: 'model.User'):
        """
        Estimates a normalized difficulty of a given text.

        :param text: text for which the difficulty is estimated
        :param language: language of the given text
        :param user: the user for which the difficulty is estimated

        :return: a value of difficulty between 0 (trivial) and 1 (the most difficult)
        """
        pass
