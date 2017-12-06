import configparser
import math
import random
import statistics

from tests_core_zeeguu.rules.user_rule import UserRule

from tests_core_zeeguu.model_test_mixin import ModelTestMixIn
from tests_core_zeeguu.rules.bookmark_rule import BookmarkRule
from zeeguu.word_scheduling.ab_testing import ABTesting
from zeeguu.word_scheduling.algorithm_service import AlgorithmService
from zeeguu.word_scheduling.algorithm_loader import AlgorithmLoader
from zeeguu.word_scheduling.algorithm_wrapper import AlgorithmWrapper
from zeeguu.word_scheduling.analysis.normal_distribution import NormalDistribution
from zeeguu.word_scheduling.arts import ArtsDiffFast, ArtsDiffSlow, ArtsRT, ArtsRandom


class WordSchedulingAlgosTest(ModelTestMixIn):
    def setUp(self):
        super().setUp()

        self.BOOKMARK_COUNT = 20

        self.user_rule = UserRule()
        self.user_rule.add_bookmarks(self.BOOKMARK_COUNT, exercises_count=1)
        self.user = self.user_rule.user

        self.config, self.algorithms = self.__get_config_with_random_algorithm_parameters(
                algorithm_count=random.randint(2, 5))
        ABTesting._algorithms = AlgorithmLoader.load_algorithms(self.config)

        AlgorithmService.update_bookmark_priority(self.db, self.user)

    """Tests for class NormalDistribution"""
    def test_calc_normal_distribution(self):
        test_values = [random.uniform(-100, 100) for _ in range(0, random.randint(10, 100))]
        mean_should_be = statistics.mean(test_values)
        sd_should_be = statistics.stdev(test_values)

        mean_to_check, sd_to_check = NormalDistribution.calc_normal_distribution(test_values)

        assert mean_to_check == mean_should_be and sd_to_check == sd_should_be

    """Tests for class ArtsDiffFast"""
    def test_arts_diff_fast_calculate(self):
        test_parameters = [random.uniform(1, 10) for _ in range(0, 5)]
        test_algorithm = ArtsDiffFast(*test_parameters)
        test_N = random.randint(5, 25)
        test_alpha = random.randint(0, 1)
        test_sd = random.uniform(1, 5)

        priority_should_be = test_parameters[0] * (test_N - test_parameters[1]) * (
            (1 - test_alpha) * test_parameters[2] * (math.e ** (test_parameters[3] * test_sd))
            + (test_alpha * test_parameters[4])
        )

        priority_to_check = test_algorithm.calculate(test_N, test_alpha, test_sd)

        assert priority_to_check == priority_should_be

    """Tests for class ArtsDiffSlow"""
    def test_arts_slow_fast_calculate(self):
        test_parameters = [random.uniform(1, 10) for _ in range(0, 5)]
        test_algorithm = ArtsDiffSlow(*test_parameters)
        test_N = random.randint(5, 25)
        test_alpha = random.randint(0, 1)
        test_sd = random.uniform(1, 5)

        priority_should_be = test_parameters[0] * (test_N - test_parameters[1]) * (
            (1 - test_alpha) * test_parameters[2] / (math.e ** (test_parameters[3] * test_sd))
            + (test_alpha * test_parameters[4])
        )

        priority_to_check = test_algorithm.calculate(test_N, test_alpha, test_sd)

        assert priority_to_check == priority_should_be

    """Tests for class AlgorithmLoader"""
    def test_create_algorithm(self):
        algorithm_should_be = self.__create_random_algorithm()

        test_parameters = self.__get_kwargs_from_algorithm(algorithm_should_be)
        algorithm_to_check = AlgorithmLoader.create_algorithm(test_parameters)

        assert algorithm_to_check == algorithm_should_be

    def test_get_dict_from_config(self):
        test_config, test_algorithm = self.__get_config_with_random_algorithm_parameters()
        test_section = test_config.sections()[0]

        dict_should_be = self.__get_kwargs_from_algorithm(test_algorithm[0])

        dict_to_check = AlgorithmLoader.get_dict_from_config(test_config[test_section])

        assert dict_to_check == dict_should_be

    def test_load_algorithms(self):
        algorithm_should_be = self.algorithms[0]

        algorithms_loaded = AlgorithmLoader.load_algorithms(self.config)
        algorithm_to_check = algorithms_loaded[0]

        assert algorithm_to_check == algorithm_should_be

    """Tests for class ABTesting"""
    def test_get_algorithm_for_id(self):
        new_bookmark = BookmarkRule(self.user).bookmark

        idx_should_be = new_bookmark.id % len(self.algorithms)
        algorithm_should_be = self.algorithms[idx_should_be]

        algorithm_to_check = ABTesting.get_algorithm_for_id(new_bookmark.id)

        assert algorithm_should_be == algorithm_to_check

    def test_get_algorithm_wrapper_by_id(self):
        new_bookmark = BookmarkRule(self.user).bookmark

        idx_should_be = new_bookmark.id % len(self.algorithms)
        algorithm_should_be = self.algorithms[idx_should_be]
        wrapper_should_be = AlgorithmWrapper(algorithm_should_be)

        algorithm_to_check = ABTesting.get_algorithm_for_id(new_bookmark.id)
        wrapper_to_check = AlgorithmWrapper(algorithm_to_check)

        assert wrapper_should_be == wrapper_to_check

    def test_load_algorithms_from_file(self):
        assert len(ABTesting._algorithms) >= 1

    def test_split_bookmarks_based_on_algorithm(self):
        bookmarks = self.user.all_bookmarks()
        count_bookmarks_to_group = len(bookmarks) - (len(bookmarks) % len(ABTesting._algorithms))
        bookmarks_to_group = bookmarks[:count_bookmarks_to_group]

        group_count_should_be = len(ABTesting._algorithms)

        groups_created_by_ABTesting = ABTesting.split_bookmarks_based_on_algorithm(bookmarks_to_group)
        group_count_to_check = len(groups_created_by_ABTesting)

        assert group_count_to_check == group_count_should_be

    def __get_config_with_random_algorithm_parameters(self, algorithm_count=1):
        algorithms = []

        config = configparser.ConfigParser()

        for i in range(0, algorithm_count):
            random_algorithm = self.__create_random_algorithm()

            algorithms.append(random_algorithm)
            config[self.faker.word() + str(i)] = self.__get_kwargs_from_algorithm(random_algorithm)

        return config, algorithms

    @classmethod
    def __get_random_algorithm_parameters(cls):
        return {
            'a': random.uniform(1, 100),
            'd': random.randint(1, 5),
            'b': random.uniform(1, 100),
            'r': random.uniform(1, 100),
            'w': random.uniform(1, 100)
        }

    @classmethod
    def __create_random_algorithm(cls):
        kwargs = cls.__get_random_algorithm_parameters()
        if random.randint(0, 1):
            new_algorithm = ArtsRT(**kwargs)
        else:
            new_algorithm = ArtsRandom(**kwargs)

        return new_algorithm

    @staticmethod
    def __get_kwargs_from_algorithm(algorithm):
        return {
            'type': type(algorithm).__name__,
            'a': str(algorithm.a),
            'd': str(algorithm.d),
            'b': str(algorithm.b),
            'r': str(algorithm.r),
            'w': str(algorithm.w)
        }
