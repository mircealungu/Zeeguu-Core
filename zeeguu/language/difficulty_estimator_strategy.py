from abc import abstractmethod


class DifficultyEstimatorStrategy:

    @classmethod
    def is_type(cls, type):
        """
        Check if the given type corresponds to the name of the difficulty estimator
        :param type:
        :return:
        """
        return type == cls.__name__

    @classmethod
    @abstractmethod
    def estimate_difficulty(cls, text, language):
        """
        Estimates a scaled difficulty of a given text. The difficulty lies between 0 and 5.
        :param text:
        :param language:
        :return:
        """
        pass