from dataclasses import dataclass


@dataclass
class SymbolDTO:
    name: str
    kind: str
    language: str
    start_line: int
    end_line: int


@dataclass
class ImportDTO:
    import_path: str
    import_name: str | None
    language: str
    line_number: int


@dataclass
class ParseResult:
    symbols: list[SymbolDTO]
    imports: list[ImportDTO]