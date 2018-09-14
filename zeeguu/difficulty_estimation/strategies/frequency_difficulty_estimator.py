from nltk import SnowballStemmer
from wordstats import Word, WordInfo
from zeeguu import model
from zeeguu.difficulty_estimation.difficulty_estimator_strategy import DifficultyEstimatorStrategy
from zeeguu.util.text import split_words_from_text
from wordstats.file_handling.loading_from_hermit import *
from collections import defaultdict

MAGIC_CONSTANT = 10


class FrequencyDifficultyEstimator(DifficultyEstimatorStrategy):
    CUSTOM_NAMES = ["frequency"]

    def __init__(self, language, user):
        super().__init__(language, user)

        freq_list = load_language_from_hermit(self.language.code)

        word_dict = dict()
        for k, v in freq_list.word_info_dict.items():
            word_dict[k] = v.frequency

        self.stemmer = SnowballStemmer(self.language.name.lower())

        self.score_map = defaultdict(int)

        for k, v in word_dict.items():
            self.score_map[self.stemmer.stem(k.lower())] += v

        max_freq = max(self.score_map.values())

        for k in self.score_map.keys():
            self.score_map[k] = (1 - self.score_map[k] / max_freq) ** 0.5

    def estimate_difficulty(self, text: str):
        """
        This estimator computes the difficulty based on how often words in the text are used in the given difficulty_estimation
        :param text: See DifficultyEstimatorStrategy
        :param language: See DifficultyEstimatorStrategy
        :param user: See DifficultyEstimatorStrategy
        :rtype: dict
        :return: The dictionary contains the keys and return types
                    normalized: float (0<=normalized<=1)
                    discrete: string [EASY, MEDIUM, HARD]
        """
        # Calculate difficulty for each word
        words = split_words_from_text(text)

        words = [self.stemmer.stem(w.lower()) for w in words]

        words_freq = defaultdict(int)
        total_words = 0
        for w in words:
            total_words += 1
            words_freq[w] += 1

        word_scores = [(1 - self.score_map.get(w, 1)) * (words_freq[w] / total_words) for w in
                       words_freq.keys()]

        # If we can't compute the text difficulty, we estimate hard
        if (len(word_scores)) == 0:
            normalized_estimate = 1.00
            words_new = 1.00
            discrete_difficulty = "HARD"
        else:
            # Median difficulty is used for discretization
            word_scores.sort()
            center = int(round(len(word_scores) / 2, 0))
            difficulty_median = word_scores[center]

            normalized_estimate = sum(word_scores) / float(len(word_scores)) * MAGIC_CONSTANT
            discrete_difficulty = self.discrete_text_difficulty(normalized_estimate)

        difficulty_scores = dict(
            normalized=normalized_estimate,  # Originally called 'score_average'
            discrete=discrete_difficulty  # Originally called 'estimated_difficulty'
        )

        return difficulty_scores

    @classmethod
    def discrete_text_difficulty(cls, median_difficulty: float):
        """
        :param median_difficulty:
        :return: a symbolic representation of the estimated difficulty
         the values are between "EASY", "MEDIUM", and "HARD"
        """
        if median_difficulty > 0.2:
            return "EASY"
        if median_difficulty > 0.1:
            return "MEDIUM"
        return "HARD"

    @classmethod
    # TODO: must test this thing
    def word_frequency(cls, w):
        """

        """

        # Assume word is difficult and unknown
        word_frequency = 1

        # Check if the user knows the word
        try:
            known_probability = known_probabilities[w]  # Value between 0 (unknown) and 1 (known)
        except KeyError:
            known_probability = None

        if known_probability is not None:
            estimated_difficulty = 1 - float(known_probability)

        return estimated_difficulty
