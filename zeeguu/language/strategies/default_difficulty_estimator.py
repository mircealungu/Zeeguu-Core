from zeeguu import model
from zeeguu.language.difficulty_estimator_strategy import DifficultyEstimatorStrategy


class DefaultDifficultyEstimator(DifficultyEstimatorStrategy):

    # The default estimator always returns a difficulty of zero
    @classmethod
    def estimate_difficulty(cls, text: str, language: 'model.Language', user: 'model.User'):
        difficulty_scores = dict(
            score_median=0,
            score_average=0,
            estimated_difficulty="EASY",

            normalized=0,
            discrete="EASY",
        )
        return difficulty_scores
