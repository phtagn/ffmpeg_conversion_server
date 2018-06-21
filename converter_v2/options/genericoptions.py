from abc import ABCMeta, abstractmethod


class IOption(metaclass=ABCMeta):
    name = ''

    @abstractmethod
    def parse(self):
        return []

class Map(IOption):
    name = 'map'

    def __init__(self, stream_number, val: int):
        assert isinstance(val, int)
        self.stream_number = stream_number
        self.map = val

    def parse(self):
        return ['-map', f'{self.stream_number}:{self.map}']