from abc import abstractmethod
from enum import Enum


class FilterBase(Enum):

    @abstractmethod
    def get_value(self) -> str:
        raise NotImplementedError()
