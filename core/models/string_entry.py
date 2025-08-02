from dataclasses import dataclass, field
from typing import Any


@dataclass
class StringEntry:
    """Represents a single translatable string entry from a file."""

    id: int
    original: str
    translated: str
    file_name: str
    line_number: int
    file_type: str = ""
    # Reference to the parser instance for saving operations
    parser_ref: Any = field(default=None, repr=False)
