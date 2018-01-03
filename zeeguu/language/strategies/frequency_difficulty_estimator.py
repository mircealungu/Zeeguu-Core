from zeeguu.language.difficulty_estimator_strategy import DifficultyEstimatorStrategy


class FrequencyDifficultyEstimator(DifficultyEstimatorStrategy):

    @classmethod
    def estimate_difficulty(cls, text, language):
        # TODO: move frequency estimator
        return 5;