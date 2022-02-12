import os
import pickle

import rpyc

from . import utils

cache_dir = '/Users/damian/PycharmProjects/gradual-elixir/.cache/'


class GeneratorsProxy(rpyc.Service):

    _generator_functions: dict = {}
    _generator_lengths: dict = {}
    finished_loading = False

    def __init__(self, _generator_functions: dict, _generator_lengths: dict):
        self._generator_functions = generator_functions
        self._generator_lengths = generator_lengths

    def exposed_get_lengths(self, function_name, base=None, level=0):
        key = function_name + (base and f'__{base}' if base else '')
        return self._generator_lengths[key][level]

    def exposed_get(self, function_name, base=None, level=0, index=0, relation_arity=1):
        print(function_name)
        key = function_name + (base and f'__{base}' if base else '')
        generator = self._generator_functions[key]
        item = generator[level][index]
        print(item)
        if relation_arity == 1:
            return utils.unparse_type(item)
        return tuple([utils.unparse_type(item[i]) for i in range(relation_arity)])


if __name__ == '__main__':
    generator_functions = {}
    generator_lengths = {}
    for name in os.listdir(cache_dir):
        file = open(cache_dir + name, 'rb')
        name = name.split('.')[0]
        print(f'Importing {name}')
        generator_functions[name] = pickle.load(file)
        file.close()
        generator_lengths[name] = [len(generator_functions[name][i]) for i in [0, 1, 2]]
    server = rpyc.ThreadedServer(
        GeneratorsProxy(generator_functions, generator_lengths), port=18812
    )
    print('Ready!')
    server.start()
