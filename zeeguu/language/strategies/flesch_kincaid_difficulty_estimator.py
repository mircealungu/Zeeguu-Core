from zeeguu import model
from zeeguu.language.difficulty_estimator_strategy import DifficultyEstimatorStrategy
import nltk
import math

nltk.download('punkt')


class FleschKincaidDifficultyEstimator(DifficultyEstimatorStrategy):
    """
    The Flesch-Kincaid readability index is a classic readability index.
    Wikipedia : https://en.wikipedia.org/wiki/Flesch–Kincaid_readability_tests
    """

    AVERAGE_SYLLABLE_LENGTH = 2.5  # Simplifies the syllable counting

    @classmethod
    def estimate_difficulty(cls, text: str, language: 'model.Language', user: 'model.User'):
        words = nltk.word_tokenize(text)

        number_of_syllables = 0
        number_of_words = 0
        for word in words:
            if word not in [',', '.', '?', '!']:  # Filter punctuation
                syllables_in_word = cls.estimate_number_of_syllables_in_word(word, language)
                number_of_syllables += syllables_in_word
                number_of_words += 1

        number_of_sentences = len(nltk.sent_tokenize(text))

        index = 206.835 - 1.015 * (number_of_words / number_of_sentences) - 84.6 * (number_of_syllables / number_of_words)

        difficulty_scores = dict(
            normalized=cls.normalize_difficulty(index),
            discrete=cls.discrete_difficulty(index)
        )

        return difficulty_scores

    @classmethod
    def estimate_number_of_syllables_in_word(cls, word: str, language: 'model.Language'):
        if len(word) < cls.AVERAGE_SYLLABLE_LENGTH:
            syllables = 1  # Always at least 1 syllable
        else:
            syllables = len(word) / cls.AVERAGE_SYLLABLE_LENGTH
        return int(math.floor(syllables))  # Truncate the number of syllables

    @classmethod
    def normalize_difficulty(cls, score: int):
        if score < 0:
            return 1
        elif score > 100:
            return 0
        else:
            return 1 - (score * 0.01)

    @classmethod
    def discrete_difficulty(cls, score: int):
        if score > 80:
            return "EASY"
        elif score > 50:
            return "MEDIUM"
        else:
            return "HARD"
