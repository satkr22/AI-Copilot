# backend/app/services/indexing/parser/parser_service.py

from dataclasses import dataclass

from tree_sitter import Language, Parser, Tree
from tree_sitter_language_pack import get_language


@dataclass(slots=True)
class ParseTree:
    tree: Tree
    source_bytes: bytes


class ParserService:
   

    def __init__(self) -> None:
        self._parsers: dict[str, Parser] = {}

    def _get_parser(self, language: str) -> Parser:
        """
        Get a cached parser for the requested language.

        Parsers are initialized lazily so we do not load every supported
        grammar when the service starts.
        """

        language = language.strip().lower()

        if not language:
            raise ValueError("Language cannot be empty.")

        parser = self._parsers.get(language)

        if parser is not None:
            return parser

        try:
            language_obj: Language = get_language(language) # type: ignore
        except Exception as exc:
            raise ValueError(
                f"Unsupported Tree-sitter language: {language!r}"
            ) from exc

        parser = Parser(language_obj)

        self._parsers[language] = parser

        return parser

    def parse_tree(
        self,
        language: str,
        source: str,
    ) -> ParseTree:
        """
        Parse source code into a Tree-sitter CST.

        Args:
            language:
                Tree-sitter language name, e.g. "python", "javascript",
                "typescript", "java", "cpp", etc.

            source:
                Source code to parse.

        Returns:
            ParseTree containing:
                - the Tree-sitter CST
                - the exact UTF-8 source bytes used for parsing

        Raises:
            ValueError:
                If the language is empty or unsupported.
        """

        source_bytes = source.encode("utf-8")

        parser = self._get_parser(language)

        tree = parser.parse(source_bytes)

        return ParseTree(
            tree=tree,
            source_bytes=source_bytes,
        )