from unittest import TestCase

from tests_zeeguu.rules.user_rule import UserRule

from tests_zeeguu.rules.language_rule import LanguageRule

from tests_zeeguu.model_test_mixin import ModelTestMixIn
from zeeguu.difficulty_estimation.strategies.flesch_kincaid_difficulty_estimator import \
    FleschKincaidDifficultyEstimator

E_EASY_TEXT = "The cat sat on the mat."
E_MEDIUM_TEXT = "This sentence, taken as a reading passage unto itself, is being used to prove a point."
E_HARD_TEXT = "The Australian platypus is seemingly a hybrid of a mammal and reptilian creature irrespectant pedigreeness accountedfor."

DE_EASY_TEXT = "Ich bin ein Berliner."
DE_MEDIUM_TEXT = "Ich bin ins Kino gegangen, um mir einen Film anzuschauen, den ich sehr spannend fand."
DE_HARD_TEXT = "Wegen Wörtern wie Frühstücksfernsehen, Fußgängerübergang und Verkehrsüberwachung liebe ich "


class FleschKincaidReadingEaseDifficultyEstimatorTest(ModelTestMixIn, TestCase):

    def setUp(self):
        super().setUp()
        self.user = UserRule().user
        self.en = LanguageRule().en
        self.de = LanguageRule().de

        self.fk_en = FleschKincaidDifficultyEstimator(self.en, self.user)
        self.fk_de = FleschKincaidDifficultyEstimator(self.de, self.user)

    # CUSTOM NAMES
    def test_recognized_by_FKIndex(self):
        name = "FKIndex"
        self.assertTrue(FleschKincaidDifficultyEstimator.has_custom_name(name))

    def test_recognized_by_FK(self):
        name = "fk"
        self.assertTrue(FleschKincaidDifficultyEstimator.has_custom_name(name))

    def test_recognized_by_flesch_kincaid(self):
        name = "flesch-kincaid"
        self.assertTrue(FleschKincaidDifficultyEstimator.has_custom_name(name))

    # NORMALIZE TESTS
    def test_normalized_above_100(self):
        d = self.fk_en.normalize_difficulty(178)
        self.assertEqual(d, 0)

    def test_normalized_100(self):
        d = self.fk_en.normalize_difficulty(100)
        self.assertEqual(d, 0)

    def test_normalized_between_100_and_0(self):
        d = self.fk_en.normalize_difficulty(50)
        self.assertEqual(d, 0.5)

    def test_normalized_0(self):
        d = self.fk_en.normalize_difficulty(0)
        self.assertEqual(d, 1)

    def test_normalized_below_0(self):
        d = self.fk_en.normalize_difficulty(-10)
        self.assertEqual(d, 1)

    # DISCRETE TESTS
    def test_discrete_above_80(self):
        d = self.fk_en.discrete_difficulty(100)
        self.assertEqual(d, 'EASY')

    def test_discrete_80(self):
        d = self.fk_en.discrete_difficulty(80)
        self.assertEqual(d, 'MEDIUM')

    def test_discrete_between_80_and_50(self):
        d = self.fk_en.discrete_difficulty(60)
        self.assertEqual(d, 'MEDIUM')

    def test_discrete_50(self):
        d = self.fk_en.discrete_difficulty(50)
        self.assertEqual(d, 'HARD')

    def test_discrete_below_50(self):
        d = self.fk_en.discrete_difficulty(30)
        self.assertEqual(d, 'HARD')

    def test_discrete_below_0(self):
        d = self.fk_en.discrete_difficulty(-10)
        self.assertEqual(d, 'HARD')

    # DIFFERENT CONSTANT VALUES
    def test_english_constants(self):
        constants = self.fk_en.get_constants_for_language()
        self.assertEqual(206.835, constants["start"])
        self.assertEqual(1.015, constants["sentence"])
        self.assertEqual(84.6, constants["word"])

    def test_german_constants(self):
        constants = self.fk_de.get_constants_for_language()
        self.assertEqual(180, constants["start"])
        self.assertEqual(1, constants["sentence"])
        self.assertEqual(58.5, constants["word"])

    # ENGLISH TESTS
    def test_english_easy(self):
        d = self.fk_en.estimate_difficulty(E_EASY_TEXT)
        self.assertEqual(d['discrete'], 'EASY')

    def test_english_medium(self):
        d = self.fk_en.estimate_difficulty(E_MEDIUM_TEXT)
        self.assertEqual(d['discrete'], 'MEDIUM')

    def test_english_hard(self):
        d = self.fk_en.estimate_difficulty(E_HARD_TEXT)
        self.assertEqual(d['discrete'], 'HARD')

    # GERMAN TESTS
    def test_german_easy(self):
        d = self.fk_de.estimate_difficulty(DE_EASY_TEXT)
        self.assertEqual('EASY', d['discrete'])

    def test_german_medium(self):
        d = self.fk_de.estimate_difficulty(DE_MEDIUM_TEXT)
        self.assertEqual('MEDIUM', d['discrete'])

    def test_german_hard(self):
        d = self.fk_de.estimate_difficulty(DE_HARD_TEXT)
        self.assertEqual('HARD', d['discrete'])
