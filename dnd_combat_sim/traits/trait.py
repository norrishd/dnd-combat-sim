import abc


class Trait(abc.ABC):
    """Base class for a special creature trait or ability."""

    def __repr__(self) -> str:
        return type(self).__name__
