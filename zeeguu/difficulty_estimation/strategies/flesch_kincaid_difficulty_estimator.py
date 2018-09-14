import nltk
import pyphen
from numpy import math

from zeeguu.difficulty_estimation.difficulty_estimator_strategy import DifficultyEstimatorStrategy
from zeeguu.util.text import split_words_from_text
from zeeguu.model import Language
from collections import Counter


class FleschKincaidDifficultyEstimator(DifficultyEstimatorStrategy):
    """


        The Flesch-Kincaid readability index is a classic readability index.
        Wikipedia : https://en.wikipedia.org/wiki/Flesch–Kincaid_readability_tests


    """

    CUSTOM_NAMES = ["fk", "fkindex", "flesch-kincaid"]

    def estimate_difficulty(self, text: str):
        '''

            Estimates the difficulty based on the Flesch-Kincaid readability index.

        :param text: See DifficultyEstimatorStrategy
        :param language: See DifficultyEstimatorStrategy
        :param user: See DifficultyEstimatorStrategy
        :rtype: dict
        :return: The dictionary contains the keys and return types
                    normalized: float (0<=normalized<=1)
                    discrete: string [EASY, MEDIUM, HARD]
        '''
        flesch_kincaid_index = self.flesch_kincaid_readability_index(text, self.language)

        difficulty_scores = dict(
            normalized=self.normalize_difficulty(flesch_kincaid_index),
            discrete=self.discrete_difficulty(flesch_kincaid_index),
            grade=self.grade_difficulty(flesch_kincaid_index)
        )

        return difficulty_scores

    def flesch_kincaid_readability_index(self, text: str, language: 'Language'):
        words = [w.lower() for w in split_words_from_text(text)]

        number_of_syllables = 0
        number_of_words = len(words)
        for word, freq in Counter(words).items():
            syllables_in_word = self.estimate_number_of_syllables_in_word_pyphen(word)
            number_of_syllables += syllables_in_word * freq

        number_of_sentences = len(nltk.sent_tokenize(text))

        constants = self.get_constants_for_language();

        index = constants["start"] - constants["sentence"] * (number_of_words / number_of_sentences) \
                - constants["word"] * (number_of_syllables / number_of_words)
        return index

    def get_constants_for_language(self):
        if self.language.code == "de":
            return {"start": 180, "sentence": 1, "word": 58.5}
        else:
            return {"start": 206.835, "sentence": 1.015, "word": 84.6}

    def estimate_number_of_syllables_in_word_pyphen(self, word: str):

        AVERAGE_SYLLABLE_LENGTH = 2.5  # Simplifies the syllable counting

        if self.language.code == "zh-CN":
            if len(word) < AVERAGE_SYLLABLE_LENGTH:
                syllables = 1  # Always at least 1 syllable
            else:
                syllables = len(word) / AVERAGE_SYLLABLE_LENGTH
            return int(math.floor(syllables))  # Truncate the number of syllables
        else:
            dic = pyphen.Pyphen(lang=self.language.code)
            syllables = len(dic.positions(word)) + 1
            return syllables

    def normalize_difficulty(self, score: int):
        if score < 0:
            return 1
        elif score > 100:
            return 0
        else:
            return round(1 - (score * 0.01), 2)

    def discrete_difficulty(self, score: int):
        if score > 80:
            return "EASY"
        elif score > 50:
            return "MEDIUM"
        else:
            return "HARD"

    def grade_difficulty(self, score: int):
        if score < 0:
            return 100
        elif score > 100:
            return 0
        else:
            return int(round(100 - score))
