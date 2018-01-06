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
    def estimate_difficulty(cls, text, language, user):
        """

            Estimates a normalized difficulty of a given text.

        :param text:
        :param language:
        :param user: the user for which the

        :return: a value of difficulty between 0 (trivial) and 1 (the most difficult)
        """
        pass
