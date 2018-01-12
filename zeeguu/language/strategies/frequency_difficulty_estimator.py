import wordstats

from zeeguu import model
from zeeguu.language.difficulty_estimator_strategy import DifficultyEstimatorStrategy
from zeeguu.the_librarian.text import split_words_from_text
from wordstats import Word, WordInfo


class FrequencyDifficultyEstimator(DifficultyEstimatorStrategy):

    @classmethod
    def estimate_difficulty(cls, text: str, language: 'model.Language', user: 'model.User'):
        word_difficulties = []

        # Calculate difficulty for each word
        words = split_words_from_text(text)

        for word in words:
            var = Word.stats(word, language.code)
            difficulty = cls.word_difficulty({}, True, Word.stats(word, language.code), word)
            word_difficulties.append(difficulty)

        # If we can't compute the text difficulty, we estimate hard
        if (len(word_difficulties)) == 0:
            return \
                dict(
                    score_median=1,
                    score_average=1,
                    estimated_difficulty=1)

        # Average difficulty for text
        difficulty_average = sum(word_difficulties) / float(len(word_difficulties))

        # Median difficulty
        word_difficulties.sort()
        center = int(round(len(word_difficulties) / 2, 0))
        difficulty_median = word_difficulties[center]

        normalized_estimate = difficulty_average

        difficulty_scores = dict(
            score_median=difficulty_median,
            score_average=difficulty_average,
            estimated_difficulty=cls.discrete_text_difficulty(difficulty_average, difficulty_median),
            # previous are for backwards compatibility reasons
            # TODO: must be removed

            normalized=normalized_estimate,
            discrete=cls.discrete_text_difficulty(difficulty_average, difficulty_median),
        )

        return difficulty_scores

    @classmethod
    def discrete_text_difficulty(cls, median_difficulty: float, average_difficulty: float):
        """

        :param median_difficulty:
        :param average_difficulty:
        :return: a symbolic representation of the estimated difficulty
         the values are between "EASY", "MEDIUM", and "HARD"
        """
        if average_difficulty < 0.3:
            return "EASY"
        if average_difficulty < 0.4:
            return "MEDIUM"
        return "HARD"

    @classmethod
    # TODO: must test this thing
    def word_difficulty(cls, known_probabilities: dict, personalized: bool, word_info: WordInfo, word: Word):
        """
        # estimate the difficulty of a word, given:
            :param word_info:
            :param known_probabilities:
            :param personalized:
            :param word:

        :return: a normalized value where 0 is (easy) and 1 is (hard)
        """

        # Assume word is difficult and unknown
        estimated_difficulty = 1.0

        # Check if the user knows the word
        try:
            known_probability = known_probabilities[word]  # Value between 0 (unknown) and 1 (known)
        except KeyError:
            known_probability = None

        if personalized and known_probability is not None:
            estimated_difficulty -= float(known_probability)
        elif word_info:
            estimated_difficulty = word_info.difficulty

        return estimated_difficulty

