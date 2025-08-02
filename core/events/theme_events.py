from .event_system import Event

class ThemeChangedEvent(Event):
    def __init__(self, theme_name: str, theme_data: dict, source: str = "ThemeService"):
        super().__init__(source)
        self.theme_name = theme_name
        self.theme_data = theme_data

    @property
    def event_type(self) -> str:
        return "theme_changed"
