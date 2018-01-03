from abc import abstractmethod


class DifficultyEstimatorStrategy:

    @classmethod
    def is_type(cls, type):
        return type == cls.__name__

    @classmethod
    @abstractmethod
    def estimate_difficulty(cls, text, language):
        pass