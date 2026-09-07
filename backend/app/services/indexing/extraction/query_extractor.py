from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from tree_sitter import Language, Node, Tree

from app.services.indexing.dto_models.models import ImportDTO, SymbolDTO, SymbolKind

QUERY_DIR = Path(__file__).resolve().parent.parent / "queries"


@dataclass(slots=True)
class RawExtractionResult:
    file_path: str
    language: str
    tree: Tree
    source_bytes: bytes
    symbols: list[SymbolDTO]
    imports: list[ImportDTO]
    symbol_nodes: dict[str, Node]


class QueryExtractor:
    """Extract symbols/imports once from a parsed Tree-sitter tree.

    Query files define the preferred boundaries. The small AST fallback keeps a
    language usable when a grammar changes its node names or a query is not
    available yet; a single bad query must never discard an entire file.
    """

    def extract(
        self,
        tree: Tree,
        source_bytes: bytes,
        file_path: str,
        language: str,
        language_obj: Language | None = None,
    ) -> RawExtractionResult:
        language = language.lower()
        matches = self._query_matches(tree, language, language_obj)
        symbols: list[SymbolDTO] = []
        imports: list[ImportDTO] = []
        symbol_nodes: dict[str, Node] = {}

        for node, kind, name_node in matches:
            if kind == "import":
                imports.extend(
                    self._imports_from_node(node, source_bytes, language, file_path)
                )
                continue
            name = (
                self._text(name_node, source_bytes)
                if name_node
                else self._anonymous_name(node)
            )
            if not name:
                continue
            symbol_kind = self._symbol_kind(kind)
            if language == "kotlin" and symbol_kind is SymbolKind.CLASS:
                # Kotlin represents enum classes with the same
                # class_declaration node; the declaration keyword is the
                # reliable discriminator.
                declaration = self._text(node, source_bytes).lstrip()
                if declaration.startswith("enum class"):
                    symbol_kind = SymbolKind.ENUM
            symbol_id = str(
                uuid5(
                    NAMESPACE_URL,
                    f"{file_path}:{node.start_byte}:{node.end_byte}:{name}",
                )
            )
            symbol = SymbolDTO(
                symbol_id=symbol_id,
                name=name,
                qualified_name=name,
                kind=symbol_kind,
                language=language,
                file_path=file_path,
                start_byte=node.start_byte,
                end_byte=node.end_byte,
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                signature=self._signature(node, source_bytes),
                docstring=self._docstring(node, source_bytes),
                content_hash=self._hash(source_bytes[node.start_byte : node.end_byte]),
            )
            if not any(existing.symbol_id == symbol_id for existing in symbols):
                symbols.append(symbol)
                symbol_nodes[symbol_id] = node

        if not symbols:
            symbols, symbol_nodes = self._fallback_symbols(
                tree.root_node, source_bytes, file_path, language
            )

        self._assign_scope(symbols)
        # Python's grammar uses the same function_definition node for
        # top-level functions and class methods. Scope makes the distinction
        # without duplicating language-specific query patterns.
        for symbol in symbols:
            if symbol.kind is SymbolKind.FUNCTION and symbol.parent_symbol_id:
                parent = next(
                    (
                        item
                        for item in symbols
                        if item.symbol_id == symbol.parent_symbol_id
                    ),
                    None,
                )
                if parent and parent.kind is SymbolKind.CLASS:
                    symbol.kind = SymbolKind.METHOD
        imports.extend(
            self._fallback_imports(
                tree.root_node, source_bytes, language, file_path, imports
            )
        )
        symbols.sort(
            key=lambda item: (item.start_byte, -(item.end_byte - item.start_byte))
        )
        imports.sort(key=lambda item: item.start_byte)
        return RawExtractionResult(
            file_path, language, tree, source_bytes, symbols, imports, symbol_nodes
        )

    def _query_matches(
        self, tree: Tree, language: str, language_obj: Language | None
    ) -> list[tuple[Node, str, Node | None]]:
        query_path = QUERY_DIR / f"{language}.scm"
        if not query_path.exists():
            return []
        try:
            from tree_sitter import Query, QueryCursor

            query_text = query_path.read_text(encoding="utf-8")
            try:
                query = (
                    language_obj.query(query_text) if language_obj is not None else None
                )
                if query is None:
                    return []
            except AttributeError:
                # tree-sitter 0.25 exposes Query through the Language object,
                # while older compatible releases accept the same constructor.
                if language_obj is None:
                    return []
                query = Query(language_obj, query_text)  # type: ignore[arg-type]
            matches: list[tuple[Node, str, Node | None]] = []
            for _pattern, captures in QueryCursor(query).matches(tree.root_node):
                outer = next(
                    (
                        self._first_node(nodes)
                        for name, nodes in captures.items()
                        if name.startswith("definition.")
                    ),
                    None,
                )
                if outer is None:
                    continue
                kind = next(
                    name.removeprefix("definition.")
                    for name in captures
                    if name.startswith("definition.")
                )
                name_node = next(
                    (
                        self._first_node(nodes)
                        for name, nodes in captures.items()
                        if name == "name"
                    ),
                    None,
                )
                matches.append((outer, kind, name_node))
            return matches
        except Exception:
            return []

    def _imports_from_node(
        self, node: Node, source: bytes, language: str, file_path: str
    ) -> list[ImportDTO]:
        statement = self._text(node, source).strip()
        results: list[ImportDTO] = []
        if language == "python":
            if statement.startswith("from "):
                match = re.match(
                    r"from\s+([.]?[^\s]+)\s+import\s+(.+)", statement, re.S
                )
                if match:
                    module, names = match.groups()
                    for item in names.split(","):
                        item = item.strip()
                        if not item:
                            continue
                        parts = re.split(r"\s+as\s+", item, maxsplit=1)
                        results.append(
                            self._import(
                                file_path,
                                language,
                                node,
                                module,
                                parts[0],
                                parts[1] if len(parts) == 2 else None,
                                source,
                            )
                        )
                    # Keep one copy of the statement text for the import
                    # header. The DTOs still retain one row per imported
                    # name for persistence, but only the first row represents
                    # the source statement itself.
                    for item in results[1:]:
                        item.raw_statement = None
            elif statement.startswith("import "):
                for item in statement[7:].split(","):
                    parts = re.split(r"\s+as\s+", item.strip(), maxsplit=1)
                    module = parts[0]
                    results.append(
                        self._import(
                            file_path,
                            language,
                            node,
                            module,
                            module.split(".")[-1],
                            parts[1] if len(parts) == 2 else None,
                            source,
                        )
                    )
        elif language in {"javascript", "typescript"}:
            match = re.search(
                r"\bfrom\s+['\"]([^'\"]+)['\"]|import\s+['\"]([^'\"]+)['\"]", statement
            )
            if match:
                module = match.group(1) or match.group(2)
                results.append(
                    self._import(file_path, language, node, module, None, None, source)
                )
        elif language == "go":
            results = [
                self._import(file_path, language, node, path, None, None, source)
                for path in re.findall(r'"([^"]+)"', statement)
            ]
            for item in results[1:]:
                item.raw_statement = None
            return results
        elif language in {"c", "cpp"}:
            match = re.match(r'#include\s*[<"]([^>"]+)[>"]', statement)
            if match:
                return [
                    self._import(
                        file_path, language, node, match.group(1), None, None, source
                    )
                ]
        elif language == "csharp":
            match = re.match(r"using\s+(?:static\s+)?([\w.]+)\s*;", statement)
            if match:
                return [
                    self._import(
                        file_path, language, node, match.group(1), None, None, source
                    )
                ]
        elif language == "ruby":
            match = re.match(r"require(?:_relative)?\s+['\"]([^'\"]+)['\"]", statement)
            if match:
                return [
                    self._import(
                        file_path, language, node, match.group(1), None, None, source
                    )
                ]
        elif language == "php":
            match = re.match(r"(?:use|require(?:_once)?)\s+([^;]+)", statement)
            if match:
                return [
                    self._import(
                        file_path,
                        language,
                        node,
                        match.group(1).strip(),
                        None,
                        None,
                        source,
                    )
                ]
        elif language in {"rust", "kotlin", "swift"}:
            match = re.search(r"(?:use|import)\s+([\\\w./:@-]+)", statement)
            if match:
                return [
                    self._import(
                        file_path, language, node, match.group(1), None, None, source
                    )
                ]
        else:
            match = re.search(r"(?:import|use)\s+([\\\w./:@-]+)", statement)
            if match:
                module = match.group(1)
                results.append(
                    self._import(file_path, language, node, module, None, None, source)
                )
        return results

    def _fallback_symbols(
        self, root: Node, source: bytes, file_path: str, language: str
    ) -> tuple[list[SymbolDTO], dict[str, Node]]:
        mapping = {
            "python": {
                "function_definition": SymbolKind.FUNCTION,
                "class_definition": SymbolKind.CLASS,
            },
            "javascript": {
                "function_declaration": SymbolKind.FUNCTION,
                "class_declaration": SymbolKind.CLASS,
                "method_definition": SymbolKind.METHOD,
            },
            "typescript": {
                "function_declaration": SymbolKind.FUNCTION,
                "class_declaration": SymbolKind.CLASS,
                "method_definition": SymbolKind.METHOD,
                "interface_declaration": SymbolKind.INTERFACE,
            },
            "java": {
                "method_declaration": SymbolKind.METHOD,
                "class_declaration": SymbolKind.CLASS,
                "interface_declaration": SymbolKind.INTERFACE,
                "enum_declaration": SymbolKind.ENUM,
            },
            "go": {
                "function_declaration": SymbolKind.FUNCTION,
                "method_declaration": SymbolKind.METHOD,
                "type_declaration": SymbolKind.TYPE_ALIAS,
            },
            "rust": {
                "function_item": SymbolKind.FUNCTION,
                "struct_item": SymbolKind.STRUCT,
                "enum_item": SymbolKind.ENUM,
                "trait_item": SymbolKind.INTERFACE,
                "type_item": SymbolKind.TYPE_ALIAS,
            },
            "c": {
                "function_definition": SymbolKind.FUNCTION,
                "struct_specifier": SymbolKind.STRUCT,
                "union_specifier": SymbolKind.STRUCT,
                "enum_specifier": SymbolKind.ENUM,
                "type_definition": SymbolKind.TYPE_ALIAS,
            },
            "cpp": {
                "function_definition": SymbolKind.FUNCTION,
                "class_specifier": SymbolKind.CLASS,
                "struct_specifier": SymbolKind.STRUCT,
                "enum_specifier": SymbolKind.ENUM,
                "type_definition": SymbolKind.TYPE_ALIAS,
            },
            "csharp": {
                "method_declaration": SymbolKind.METHOD,
                "class_declaration": SymbolKind.CLASS,
                "interface_declaration": SymbolKind.INTERFACE,
                "struct_declaration": SymbolKind.STRUCT,
                "enum_declaration": SymbolKind.ENUM,
            },
            "kotlin": {
                "function_declaration": SymbolKind.FUNCTION,
                "class_declaration": SymbolKind.CLASS,
                "type_alias": SymbolKind.TYPE_ALIAS,
            },
            "php": {
                "function_definition": SymbolKind.FUNCTION,
                "class_declaration": SymbolKind.CLASS,
                "interface_declaration": SymbolKind.INTERFACE,
                "method_declaration": SymbolKind.METHOD,
            },
            "ruby": {
                "method": SymbolKind.METHOD,
                "singleton_method": SymbolKind.METHOD,
                "class": SymbolKind.CLASS,
            },
            "swift": {
                "function_declaration": SymbolKind.FUNCTION,
                "class_declaration": SymbolKind.CLASS,
                "struct_declaration": SymbolKind.STRUCT,
                "protocol_declaration": SymbolKind.INTERFACE,
                "enum_declaration": SymbolKind.ENUM,
                "typealias_declaration": SymbolKind.TYPE_ALIAS,
            },
        }.get(language, {})
        symbols: list[SymbolDTO] = []
        nodes: dict[str, Node] = {}
        for node in self._walk(root):
            kind = mapping.get(node.type)
            if kind is None:
                continue
            name_node = node.child_by_field_name("name")
            name = (
                self._text(name_node, source)
                if name_node
                else self._anonymous_name(node)
            )
            if language == "kotlin" and kind is SymbolKind.CLASS:
                if self._text(node, source).lstrip().startswith("enum class"):
                    kind = SymbolKind.ENUM
            symbol_id = str(
                uuid5(
                    NAMESPACE_URL,
                    f"{file_path}:{node.start_byte}:{node.end_byte}:{name}",
                )
            )
            symbols.append(
                SymbolDTO(
                    symbol_id,
                    name,
                    name,
                    kind,
                    language,
                    file_path,
                    node.start_byte,
                    node.end_byte,
                    node.start_point[0] + 1,
                    node.end_point[0] + 1,
                    signature=self._signature(node, source),
                    docstring=self._docstring(node, source),
                    content_hash=self._hash(source[node.start_byte : node.end_byte]),
                )
            )
            nodes[symbol_id] = node
        return symbols, nodes

    def _fallback_imports(
        self,
        root: Node,
        source: bytes,
        language: str,
        file_path: str,
        existing: list[ImportDTO],
    ) -> list[ImportDTO]:
        known = {(item.start_byte, item.end_byte) for item in existing}
        types = {
            "import_statement",
            "import_from_statement",
            "import_declaration",
            "use_declaration",
            "using_directive",
            "namespace_use_declaration",
            "import_header",
            "preproc_include",
        }
        results: list[ImportDTO] = []
        for node in self._walk(root):
            if node.type not in types or (node.start_byte, node.end_byte) in known:
                continue
            results.extend(self._imports_from_node(node, source, language, file_path))
        return results

    def _assign_scope(self, symbols: list[SymbolDTO]) -> None:
        symbols.sort(
            key=lambda item: (item.start_byte, -(item.end_byte - item.start_byte))
        )
        for symbol in symbols:
            parents = [
                candidate
                for candidate in symbols
                if candidate.symbol_id != symbol.symbol_id
                and candidate.start_byte <= symbol.start_byte
                and candidate.end_byte >= symbol.end_byte
            ]
            if not parents:
                continue
            parent = min(parents, key=lambda item: item.end_byte - item.start_byte)
            symbol.parent_symbol_id = parent.symbol_id
            symbol.parent_name = parent.name
            symbol.qualified_name = f"{parent.qualified_name}.{symbol.name}"

    def _import(
        self,
        file_path: str,
        language: str,
        node: Node,
        path: str,
        name: str | None,
        alias: str | None,
        source: bytes,
    ) -> ImportDTO:
        return ImportDTO(
            str(
                uuid5(
                    NAMESPACE_URL, f"{file_path}:import:{node.start_byte}:{path}:{name}"
                )
            ),
            path,
            name,
            alias,
            path.startswith("."),
            language,
            file_path,
            node.start_point[0] + 1,
            node.start_byte,
            node.end_byte,
            self._text(node, source),
        )

    @staticmethod
    def _symbol_kind(kind: str) -> SymbolKind:
        try:
            return SymbolKind(kind)
        except ValueError:
            return SymbolKind.FUNCTION

    @staticmethod
    def _walk(node: Node):
        yield node
        for child in node.children:
            yield from QueryExtractor._walk(child)

    @staticmethod
    def _text(node: Node | None, source: bytes) -> str:
        return (
            ""
            if node is None
            else source[node.start_byte : node.end_byte].decode(
                "utf-8", errors="replace"
            )
        )

    @staticmethod
    def _first_node(value) -> Node | None:
        if isinstance(value, (list, tuple)):
            return value[0] if value else None
        return value

    @staticmethod
    def _hash(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    def _anonymous_name(self, node: Node) -> str:
        return f"<anonymous:{node.start_point[0] + 1}>"

    def _signature(self, node: Node, source: bytes) -> str:
        text = self._text(node, source).splitlines()[0].strip()
        return text[:500]

    def _docstring(self, node: Node, source: bytes) -> str | None:
        for child in node.children:
            if child.type in {"block", "class_body"}:
                for nested in child.children:
                    if nested.type in {"expression_statement", "string", "comment"}:
                        value = self._text(nested, source).strip()
                        if value:
                            return value
                    # break
        return None
