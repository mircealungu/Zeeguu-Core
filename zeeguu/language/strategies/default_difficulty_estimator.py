from zeeguu import model
from zeeguu.language.difficulty_estimator_strategy import DifficultyEstimatorStrategy


class DefaultDifficultyEstimator(DifficultyEstimatorStrategy):

    # The default estimator always returns a difficulty of zero
    @classmethod
    def estimate_difficulty(cls, text: str, language: 'model.Language', user: 'model.User'):
        '''
        The default difficulty estimator. Used when no matching estimator was found by the factory.
        :param text: See DifficultyEstimatorStrategy
        :param language: See DifficultyEstimatorStrategy
        :param user: See DifficultyEstimatorStrategy
        :rtype: dict
        :return: The dictionary contains the keys and return types
                score_median:float,
                score_average:float,
                estimated_difficulty:str,
                normalized:float,
                and discrete:str
        '''
        difficulty_scores = dict(
            score_median=0.0,
            score_average=0.0,
            estimated_difficulty="EASY",

            normalized=0.0,
            discrete="EASY",
        )
        return difficulty_scores
