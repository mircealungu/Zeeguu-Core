from abc import abstractmethod


class DifficultyEstimatorStrategy:
    @classmethod
    def is_type(cls, estimator_name : str):
        """
        Check if the given type corresponds to the name of the difficulty estimator
        :param type: string value of the class name, if this doesn't correspond with the actual implementing
            class name false is returned.
        :return:
        """
        return estimator_name == cls.__name__

    @classmethod
    @abstractmethod
    def estimate_difficulty(cls, text, language, user):
        """
        Estimates a normalized difficulty of a given text.

        :param text: text for which the difficulty is estimated
        :param language: language of the given text
        :param user: the user for which the difficulty is estimated

        :return: a value of difficulty between 0 (trivial) and 1 (the most difficult)
        """
        pass
