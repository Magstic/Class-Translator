class HighlightingService:
    """Service to detect characters not encodable in EUC-KR."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    def set_enabled(self, enabled: bool):
        """Enable or disable the highlighting feature."""
        self.enabled = enabled

    def is_valid(self, text: str) -> bool:
        """Check if the entire string is valid in EUC-KR."""
        if not self.enabled or not text:
            return True
        try:
            text.encode("euc-kr")
            return True
        except UnicodeEncodeError:
            return False

    def get_invalid_ranges(self, text: str) -> list[tuple[int, int]]:
        """Get start and end indices of invalid character sequences."""
        if not self.enabled or not text:
            return []

        ranges = []
        in_invalid_sequence = False
        start = -1

        for i, char in enumerate(text):
            try:
                char.encode("euc-kr")
                if in_invalid_sequence:
                    # End of an invalid sequence
                    ranges.append((start, i))
                    in_invalid_sequence = False
            except UnicodeEncodeError:
                if not in_invalid_sequence:
                    # Start of a new invalid sequence
                    in_invalid_sequence = True
                    start = i

        if in_invalid_sequence:
            # The string ends with an invalid sequence
            ranges.append((start, len(text)))

        return ranges
