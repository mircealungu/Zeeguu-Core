from zeeguu import model
from zeeguu.difficulty_estimation.difficulty_estimator_strategy import DifficultyEstimatorStrategy


class DefaultDifficultyEstimator(DifficultyEstimatorStrategy):

    # The default estimator always returns a difficulty of zero
    @classmethod
    def estimate_difficulty(cls, text: str):
        '''
        The default difficulty estimator. Used when no matching estimator was found by the factory.
        :param text: See DifficultyEstimatorStrategy
        :param language: See DifficultyEstimatorStrategy
        :param user: See DifficultyEstimatorStrategy
        :rtype: dict
        :return: The dictionary contains the keys and return types
                    normalized: float (0<=normalized<=1)
                    discrete: string [EASY, MEDIUM, HARD]
        '''
        difficulty_scores = dict(
            normalized=0.0,
            discrete="EASY",
        )
        return difficulty_scores
