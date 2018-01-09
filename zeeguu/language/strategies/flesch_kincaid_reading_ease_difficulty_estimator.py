from zeeguu.language.difficulty_estimator_strategy import DifficultyEstimatorStrategy
import nltk
nltk.download('punkt')


class FleschKincaidReadingEaseDifficultyEstimator(DifficultyEstimatorStrategy):
    """
    The Flesch-Kincaid readability index is a classic readability index.
    Wikipedia : https://en.wikipedia.org/wiki/Flesch–Kincaid_readability_tests
    """

    AVERAGE_SYLLABLE_LENGTH = 3  # Simplifies the syllable counting

    @classmethod
    def estimate_difficulty(cls, text, language, user):
        words = nltk.word_tokenize(text)

        number_of_syllables = 0
        number_of_words = 0
        for word in words:
            if word not in [',', '.', '?', '!']:  # Filter punctuation
                syllables = len(word) / cls.AVERAGE_SYLLABLE_LENGTH
                syllables_in_word = round(syllables)  # Round instead of truncate
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
    def normalize_difficulty(cls, score):
        if score < 0:
            return 1
        elif score > 100:
            return 0
        else:
            return 1 - (score * 0.01)

    @classmethod
    def discrete_difficulty(cls, score):
        if score > 80:
            return "EASY"
        elif score > 50:
            return "MEDIUM"
        else:
            return "HARD"
