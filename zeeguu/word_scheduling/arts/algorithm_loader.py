import importlib

import zeeguu


class AlgorithmLoader:
    @classmethod
    def create_algorithm(cls, parameters):
        try:
            algorithm_name = parameters['type']
            del parameters['type']

            parameters_converted = {key: float(val) for (key, val) in parameters.items()}

            algorithm_class = getattr(importlib.import_module('zeeguu.word_scheduling.arts'), algorithm_name)
            return algorithm_class(**parameters_converted)

        except AttributeError as e:
            zeeguu.log('The specified algorithm class could not be found.')
            zeeguu.log(str(e))
            exit(-1)

    @classmethod
    def get_dict_from_config(cls, section):
        keys = [key for key in section]
        vals = [val for val in section.values()]
        return dict(zip(keys, vals))

    @classmethod
    def load_algorithms(cls, config):
        algorithms = []
        for s in config.sections():
            parameters = cls.get_dict_from_config(config[s])
            new_algorithm = cls.create_algorithm(parameters)
            algorithms.append(new_algorithm)

        return algorithms
