from dataclasses import dataclass
from enum import Enum


class StrEnum(str, Enum):
    """String-valued enum compatible with Python versions before 3.11."""
    def __str__(self) -> str:
        return self.value


# ---------------------------------------------------------
# Enums
# ---------------------------------------------------------

class SymbolKind(StrEnum):
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"


class ChunkType(StrEnum):
    FILE = "file"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"


class ProviderType(StrEnum):
    JCODE = "jcode"
    SYMLENS = "symlens"
    TREE_SITTER = "tree_sitter"


# ---------------------------------------------------------
# DTOs
# ---------------------------------------------------------

@dataclass(slots=True)
class SymbolDTO:
    name: str
    kind: SymbolKind
    language: str

    start_line: int
    end_line: int

    # Parent symbol name (None for top-level symbols)
    parent_name: str | None = None


@dataclass(slots=True)
class ImportDTO:
    import_path: str
    import_name: str | None

    language: str
    line_number: int


@dataclass(slots=True)
class CodeChunkDTO:
    chunk_type: ChunkType

    # None for whole-file chunks
    symbol_name: str | None

    start_line: int
    end_line: int

    # Actual source code contained in the chunk
    content: str

    provider: ProviderType

    # Approximate token count
    token_count: int


@dataclass(slots=True)
class ParseResultDTO:
    symbols: list[SymbolDTO]
    imports: list[ImportDTO]
    chunks: list[CodeChunkDTO]