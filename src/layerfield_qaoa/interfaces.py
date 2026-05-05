from __future__ import annotations

from abc import ABC, abstractmethod
import numpy as np


class MarketPort(ABC):
    @staticmethod
    @abstractmethod
    def build(cfg, rng: np.random.Generator):
        raise NotImplementedError


class QuboPort(ABC):
    @staticmethod
    @abstractmethod
    def build(mu: np.ndarray, sigma: np.ndarray, cfg):
        raise NotImplementedError


class ExecutorPort(ABC):
    @abstractmethod
    def run(self, params: np.ndarray, shots: int, rng: np.random.Generator):
        raise NotImplementedError


class SearchPort(ABC):
    @abstractmethod
    def suggest(self, rng: np.random.Generator) -> np.ndarray:
        raise NotImplementedError

    @abstractmethod
    def observe(self, x: np.ndarray, y: float, yvar: float) -> None:
        raise NotImplementedError


class TracePort(ABC):
    @abstractmethod
    def append(self, params: np.ndarray, stats) -> None:
        raise NotImplementedError

    @abstractmethod
    def build(self):
        raise NotImplementedError


__all__ = ['MarketPort', 'QuboPort', 'ExecutorPort', 'SearchPort', 'TracePort']
