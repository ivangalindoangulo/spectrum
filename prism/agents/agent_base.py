from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """
    Abstract base class for all Agents in the pipeline.
    """
    def __init__(self, name: str):
        self.name = name

    def log(self, message: str):
        print(f"[{self.name}] {message}")
