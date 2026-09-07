from dataclasses import dataclass, field
from enum import Enum


class StrEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class SymbolKind(StrEnum):
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    INTERFACE = "interface"
    STRUCT = "struct"
    ENUM = "enum"
    TYPE_ALIAS = "type_alias"


class ChunkType(StrEnum):
    FILE = "file"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    INTERFACE = "interface"
    STRUCT = "struct"
    ENUM = "enum"
    TYPE_ALIAS = "type_alias"
    GAP = "gap"
    MERGED = "merged"


class ChunkOrigin(StrEnum):
    QUERY_SYMBOL = "query_symbol"
    QUERY_SYMBOL_SPLIT = "query_symbol_split"
    CAST_GAP = "cast_gap"
    MERGED = "merged"


class ProviderType(StrEnum):
    JCODE = "jcode"
    SYMLENS = "symlens"


@dataclass(slots=True)
class SymbolDTO:
    symbol_id: str
    name: str
    qualified_name: str
    kind: SymbolKind
    language: str
    file_path: str
    start_byte: int
    end_byte: int
    start_line: int
    end_line: int
    parent_symbol_id: str | None = None
    parent_name: str | None = None
    signature: str | None = None
    docstring: str | None = None
    content_hash: str | None = None


@dataclass(slots=True)
class ImportDTO:
    import_id: str
    import_path: str
    import_name: str | None
    alias: str | None = None
    is_relative: bool = False
    language: str = ""
    file_path: str = ""
    line_number: int = 0
    start_byte: int = 0
    end_byte: int = 0
    raw_statement: str | None = None


@dataclass(slots=True)
class CodeChunkDTO:
    chunk_id: str
    chunk_type: ChunkType
    origin: ChunkOrigin
    file_path: str
    language: str
    symbol_ids: list[str] = field(default_factory=list)
    symbol_names: list[str] = field(default_factory=list)
    scope_chain: list[str] = field(default_factory=list)
    start_byte: int = 0
    end_byte: int = 0
    start_line: int = 0
    end_line: int = 0
    content: str = ""
    enriched_content: str | None = None
    contextual_summary: str | None = None
    is_partial: bool = False
    part_index: int | None = None
    part_total: int | None = None
    content_hash: str = ""
    provider: ProviderType = ProviderType.JCODE
    token_count: int = 0


@dataclass(slots=True)
class ParseResultDTO:
    file_path: str
    language: str
    file_content_hash: str
    symbols: list[SymbolDTO]
    imports: list[ImportDTO]
    chunks: list[CodeChunkDTO]
