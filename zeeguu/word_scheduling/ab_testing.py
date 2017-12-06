import configparser

import zeeguu.util.configuration as utils
from zeeguu.word_scheduling.algorithm_loader import AlgorithmLoader
from zeeguu.word_scheduling.algorithm_wrapper import AlgorithmWrapper


class ABTesting:
    _config_file = utils.load_config_file('WORD_SCHEDULING_ALGORITHM_CONFIG')

    _config = configparser.ConfigParser()
    _config.read(_config_file)
    _algorithms = AlgorithmLoader.load_algorithms(_config)

    @classmethod
    def get_algorithm_for_id(cls, id):
        """Returns an algorithm specified in WORD_SCHEDULING_ALGORITHM_CONFIG based on the modulo
        of the ID of the object and the number of algorithms

        :param id: An Integer, for which the algorithm should be returned
        :return: An AlgorithmWrapper containing an ArtsRT object with the parameters
                 specified in WORD_SCHEDULING_ALGORITHM_CONFIG
        """
        idx = cls.__get_algorithm_index_for_id(id)
        return cls._algorithms[idx]

    @classmethod
    def get_algorithm_wrapper_for_id(cls, id):
        algorithm = cls.get_algorithm_for_id(id)
        return AlgorithmWrapper(algorithm)

    @classmethod
    def split_bookmarks_based_on_algorithm(cls, bookmarks):
        groups = []
        for i in range(0, len(cls._algorithms)):
            groups.append([])

        for i in range(0, len(bookmarks)):
            group_idx = cls.__get_algorithm_index_for_id(bookmarks[i].id)
            groups[group_idx].append(bookmarks[i])

        return groups

    @classmethod
    def __get_algorithm_index_for_id(cls, id):
        count_algorithms = len(cls._algorithms)
        return divmod(id, count_algorithms)[1]
