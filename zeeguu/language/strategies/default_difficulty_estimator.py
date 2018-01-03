from zeeguu.language.difficulty_estimator_strategy import DifficultyEstimatorStrategy


class DefaultDifficultyEstimator(DifficultyEstimatorStrategy):

    # The default estimator always returns a difficulty of zero
    @classmethod
    def estimate_difficulty(cls, text, language):
        return 0;