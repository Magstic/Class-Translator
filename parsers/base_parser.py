from abc import ABC, abstractmethod


class BaseParser(ABC):
    """Abstract base class for file parsers."""

    @abstractmethod
    def get_utf8_strings(self):
        """Extract all UTF-8 strings from the file."""
        pass

    @abstractmethod
    def update_utf8_string(self, index, new_string):
        """Update a specific UTF-8 string by its index."""
        pass

    @abstractmethod
    def save(self, output_path):
        """Save the modified file content to a given path."""
        pass
