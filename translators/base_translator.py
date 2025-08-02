from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseTranslator(ABC):
    """Abstract base class for all translator plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the translator."""
        pass

    @abstractmethod
    def translate(
        self, text: str, dest_lang: str = "zh-cn", src_lang: str = "ko"
    ) -> str:
        """Translate the given text."""
        pass

    def is_available(self) -> bool:
        """Check if the translator is available (e.g., dependencies installed)."""
        return True

    @abstractmethod
    def get_configurable_rules(self) -> Dict[str, Any]:
        """Returns a dictionary of rules that can be configured by the user."""
        pass

    @abstractmethod
    def update_rules(self, new_rules: Dict[str, Any]):
        """Updates the translator's rules with new values from the user."""
        pass
