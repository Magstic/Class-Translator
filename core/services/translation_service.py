from typing import List, Dict

# Import translator classes directly to support PyInstaller's one-file mode
from translators.base_translator import BaseTranslator
from translators.light_google_translator import LightGoogleTranslator


class TranslationService:
    """Manages and provides access to translation engines."""

    def __init__(self):
        self.engines = self._load_engines()
        self.active_engine = None
        self.max_concurrent_requests = 5  # Default to 5 concurrent requests
        if self.engines:
            self.set_active_engine(list(self.engines.keys())[0])

    def _load_engines(self) -> Dict:
        """Loads all available translator plugins from a static list."""
        engines = {}

        # A static list of all translator classes to be loaded.
        # This is more robust for packaging with PyInstaller.
        translator_classes = [
            LightGoogleTranslator,
        ]

        for translator_class in translator_classes:
            try:
                # Ensure it's a valid translator plugin
                if (
                    issubclass(translator_class, BaseTranslator)
                    and translator_class is not BaseTranslator
                ):
                    instance = translator_class()
                    if instance.is_available():
                        engines[instance.name] = instance
                        print(f"Loaded translation engine: {instance.name}")
                    else:
                        print(
                            f"Translation engine '{instance.name}' is not available (check dependencies)."
                        )
            except Exception as e:
                # Use __name__ to get the class name for a more informative error
                print(f"Failed to load translation engine {translator_class.__name__}: {e}")

        return engines

    def get_available_engines(self) -> List[str]:
        """Returns a list of names of the available translation engines."""
        return list(self.engines.keys())

    def get_translator_names(self):
        """Returns a list of available translator names."""
        return list(self.engines.keys())

    def get_active_engine_rules(self):
        """Gets the configurable rules from the currently active translation engine."""
        if self.active_engine:
            return self.active_engine.get_configurable_rules()
        return {}

    def update_active_engine_rules(self, new_rules):
        """Updates the configurable rules for the currently active translation engine."""
        if self.active_engine:
            self.active_engine.update_rules(new_rules)

    def set_active_engine(self, name: str):
        """Sets the currently active translation engine."""
        if name in self.engines:
            self.active_engine = self.engines[name]
        else:
            raise ValueError(f"Translation engine '{name}' not found.")

    def translate(
        self, text: str, dest_lang: str = "zh-cn", src_lang: str = "ko"
    ) -> str:
        """Translates text using the active engine, passing language parameters."""
        if not self.active_engine:
            raise ValueError("No active translation engine set.")
        # Correctly pass all arguments to the underlying plugin.
        return self.active_engine.translate(
            text, dest_lang=dest_lang, src_lang=src_lang
        )

    def get_max_concurrent_requests(self) -> int:
        """Returns the maximum number of concurrent translation requests."""
        return self.max_concurrent_requests

    def set_max_concurrent_requests(self, value: int):
        """Sets the maximum number of concurrent translation requests."""
        self.max_concurrent_requests = max(1, value)  # Ensure at least 1
