from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from tree_sitter import Language, Node, Query, Tree

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

    # Keyword-like names that must never appear as extracted symbol names.
    # Each language may add its own; the superset catches false positives
    # across grammars that reuse node types in unexpected contexts (e.g. a
    # return_statement misclassified as a method_definition).
    _KEYWORDS: frozenset[str] = frozenset(
        {
            # JavaScript / TypeScript
            "return",
            "if",
            "else",
            "for",
            "while",
            "do",
            "switch",
            "case",
            "default",
            "break",
            "continue",
            "throw",
            "try",
            "catch",
            "finally",
            "new",
            "this",
            "super",
            "typeof",
            "instanceof",
            "void",
            "delete",
            "in",
            "of",
            "yield",
            "await",
            "async",
            "const",
            "let",
            "var",
            "function",
            "class",
            "import",
            "export",
            "from",
            "as",
            "static",
            "get",
            "set",
            "extends",
            "implements",
            "interface",
            "type",
            "enum",
            "namespace",
            "module",
            "declare",
            "readonly",
            "abstract",
            "public",
            "private",
            "protected",
            "any",
            "boolean",
            "number",
            "string",
            "never",
            "unknown",
            "null",
            "undefined",
            "true",
            "false",
            "require",
            # Python
            "and",
            "or",
            "not",
            "is",
            "lambda",
            "pass",
            "with",
            "raise",
            "except",
            "elif",
            "global",
            "nonlocal",
            "assert",
            "del",
            "None",
            "True",
            "False",
            # Java / Kotlin / C# / general
            "package",
            "synchronized",
            "volatile",
            "transient",
            "native",
            "strictfp",
            "goto",
            "final",
            "operator",
            "explicit",
            "virtual",
            "override",
            "sealed",
            "internal",
            "extern",
            "unsigned",
            "signed",
            "extern",
            "unsigned",
            "sizeof",
            "typedef",
            "union",
            "struct",
            "where",
            "select",
            "when",
            "object",
            "val",
            "fun",
            "data",
            "inner",
            "out",
            "ref",
            "params",
            "lock",
            "fixed",
            "stackalloc",
            "checked",
            "unchecked",
            "event",
            "delegate",
            "add",
            "remove",
            "value",
            "init",
            "any",
            "boolean",
            "number",
            "string",
            "never",
            "unknown",
            "require",
            "goto",
            "final",
            "operator",
            "explicit",
            "virtual",
            "override",
            "sealed",
            "internal",
        }
    )

    # Keywords that are only invalid in specific languages.  A name that
    # appears here is rejected only when the file language matches.
    _LANGUAGE_KEYWORDS: dict[str, frozenset[str]] = {
        "c": frozenset({"register", "goto", "auto", "union"}),
        "cpp": frozenset({"register", "goto", "auto", "union", "explicit", "virtual", "operator"}),
        "java": frozenset({"synchronized", "volatile", "transient", "native", "strictfp", "goto"}),
        "csharp": frozenset({"virtual", "override", "sealed", "internal", "extern", "where", "select", "object", "out", "ref", "params", "lock", "fixed", "stackalloc", "checked", "unchecked", "event", "delegate", "add", "remove", "value", "init"}),
        "kotlin": frozenset({"val", "fun", "data", "inner", "object", "when", "sealed", "init"}),
        "typescript": frozenset({"any", "boolean", "number", "string", "never", "unknown", "require"}),
        "javascript": frozenset({"require"}),
    }

    def __init__(self) -> None:
        # Reading the .scm file and compiling it into a tree-sitter Query is
        # the same work for every file of a given language. Doing it once per
        # file (the previous behaviour) dominated runtime on large repos;
        # caching by language turns O(files) compiles into O(languages).
        # A query is compiled against a specific Tree-sitter grammar. TS and
        # TSX share the application language name used by persistence, but
        # their Language objects are different and must not share Query
        # instances.
        self._query_cache: dict[tuple[str, int], Query] = {}

    def extract(
        self,
        tree: Tree,
        source_bytes: bytes,
        file_path: str,
        language: str,
        language_obj: Language | None = None,
    ) -> RawExtractionResult:
        language = language.lower()
        matches = self._query_matches(tree, language, language_obj, source_bytes)
        symbols: list[SymbolDTO] = []
        imports: list[ImportDTO] = []
        symbol_nodes: dict[str, Node] = {}

        for node, kind, name_node in matches:
            if kind == "import":
                imports.extend(
                    self._imports_from_node(node, source_bytes, language, file_path)
                )
                continue
            node = self._definition_boundary(node)
            name = self._valid_name(name_node, source_bytes, node, language)
            if len(name) > 255:
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

        # Fallback extraction is an error-recovery path. Running a full AST
        # walk after every successful query doubled indexing work for healthy
        # files, so only use it when the query returned nothing or parsing
        # reported errors.
        if not symbols or getattr(tree.root_node, "has_error", False):
            fallback_symbols, fallback_nodes = self._fallback_symbols(
                tree.root_node, source_bytes, file_path, language
            )
            known_spans = {
                (item.start_byte, item.end_byte, item.name) for item in symbols
            }
            for fallback in fallback_symbols:
                key = (fallback.start_byte, fallback.end_byte, fallback.name)
                if key in known_spans:
                    continue
                symbols.append(fallback)
                symbol_nodes[fallback.symbol_id] = fallback_nodes[fallback.symbol_id]
                known_spans.add(key)

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
        self, tree: Tree, language: str, language_obj: Language | None,
        source_bytes: bytes,
    ) -> list[tuple[Node, str, Node | None]]:
        query = self._compiled_query(language, language_obj)
        if query is None:
            return []
        from tree_sitter import QueryCursor

        try:
            matches: list[tuple[Node, str, Node | None]] = []
            seen_spans: set[tuple[int, int]] = set()
            for _pattern, captures in QueryCursor(query).matches(tree.root_node):
                # Each pattern match has exactly one definition.* capture
                # and exactly one @name capture.  Walk the capture dict
                # once instead of calling next() repeatedly.
                outer: Node | None = None
                kind: str | None = None
                name_node: Node | None = None
                for capture_name, nodes in captures.items():
                    if capture_name.startswith("definition."):
                        outer = self._first_node(nodes)
                        kind = capture_name.removeprefix("definition.")
                    elif capture_name == "name":
                        name_node = self._first_node(nodes)
                if outer is None or kind is None:
                    continue
                # A definition without a discoverable name is either a
                # query coverage gap (pattern missing @name) or a false
                # match (e.g. nested struct inside a typedef).  Skip it;
                # the fallback walk handles genuinely anonymous constructs
                # like `struct { int x; } var;`.
                if name_node is None:
                    continue
                # Skip duplicates: the same source range can be matched by
                # multiple query patterns (e.g. a method_definition inside a
                # class also matches a function_declaration pattern).  The
                # first match (outermost pattern) wins.
                span = (outer.start_byte, outer.end_byte)
                if span in seen_spans:
                    continue
                seen_spans.add(span)
                # Validate that the name node is actually a descendant of the
                # definition node.  When the name belongs to a different (e.g.
                # nested) node, the pattern match is ambiguous and must be
                # discarded.
                if name_node is not None and not self._is_descendant_of(
                    name_node, outer
                ):
                    continue
                # Reject impossible names: keywords, empty strings, and names
                # that look like operators or punctuation.  When a query
                # pattern matched a definition node but the name is a keyword
                # (e.g. ``return`` in a JSX context misclassified as a
                # method), drop the entire match — an anonymous placeholder
                # would still pollute embeddings and graph construction.
                if name_node is not None:
                    name_text = self._text(name_node, source_bytes)
                    if self._is_invalid_name(name_text or "", language):
                        continue
                    if len(name_text) > 255:
                        # repository_symbols.name is VARCHAR(255). A larger
                        # value means the query captured more than an
                        # identifier; reject the malformed match.
                        continue
                matches.append((outer, kind, name_node))
            return matches
        except Exception:
            return []

    def _compiled_query(self, language: str, language_obj: Language | None) -> Query | None:
        cache_key = (language, id(language_obj) if language_obj is not None else 0)
        if cache_key in self._query_cache:
            return self._query_cache[cache_key]
        query = self._compile_query(language, language_obj)
        # Only cache successful compilations.  Caching None would permanently
        # disable a language even when a valid language_obj becomes available
        # later (e.g. after lazy grammar loading completes).
        if query is not None:
            self._query_cache[cache_key] = query
        return query

    @staticmethod
    def _compile_query(language: str, language_obj: Language | None) -> Query | None:
        query_path = QUERY_DIR / f"{language}.scm"
        if not query_path.exists():
            return None
        try:
            query_text = query_path.read_text(encoding="utf-8")
            try:
                query = (
                    language_obj.query(query_text) if language_obj is not None else None
                )
            except AttributeError:
                # tree-sitter 0.25 exposes Query through the Language object,
                # while older compatible releases accept the same constructor.
                if language_obj is None:
                    return None
                query = Query(language_obj, query_text)  # type: ignore[arg-type]
            return query
        except Exception:
            return None

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
                    # Strip parenthesized grouping: `from foo import (a, b)`
                    names = names.strip()
                    if names.startswith("(") and names.endswith(")"):
                        names = names[1:-1]
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
                    for item in results[1:]:
                        item.raw_statement = None
            elif statement.startswith("import "):
                names = statement[7:].strip()
                if names.startswith("(") and names.endswith(")"):
                    names = names[1:-1]
                for item in names.split(","):
                    item = item.strip()
                    if not item:
                        continue
                    parts = re.split(r"\s+as\s+", item, maxsplit=1)
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
            # ES module imports: preserve named/default/namespace imports.
            # import { foo, bar as baz } from './mod'
            # import defaultExport, { named } from './mod'
            # import * as ns from './mod'
            # import './side-effect'
            match = re.search(
                r"\bfrom\s+['\"]([^'\"]+)['\"]|import\s+['\"]([^'\"]+)['\"]",
                statement,
            )
            module = match.group(1) or match.group(2) if match else None
            # Extract the import clause (everything between "import" and
            # "from" or end-of-statement).
            clause = statement
            if match:
                clause = statement[: match.start()]
            clause = re.sub(r"^import\s+", "", clause).strip()
            if not clause and module:
                # Side-effect import: import './side-effect'
                results.append(
                    self._import(
                        file_path, language, node, module, None, None, source
                    )
                )
            elif clause:
                # Handle `import * as ns from '...'` and `import type { ... }`
                # and `import defaultExport, { named } from '...'`
                for part in self._split_import_clause(clause):
                    if not part:
                        continue
                    parts = re.split(r"\s+as\s+", part, maxsplit=1)
                    imported_name = parts[0].strip()
                    alias = parts[1].strip() if len(parts) == 2 else None
                    results.append(
                        self._import(
                            file_path,
                            language,
                            node,
                            module or "",
                            imported_name,
                            alias,
                            source,
                        )
                    )
            if not results:
                results.append(
                    self._import(
                        file_path, language, node, module or "", None, None, source
                    )
                )
            for item in results[1:]:
                item.raw_statement = None
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
                "generator_function_declaration": SymbolKind.FUNCTION,
                "class_declaration": SymbolKind.CLASS,
                "method_definition": SymbolKind.METHOD,
            },
            "typescript": {
                "function_declaration": SymbolKind.FUNCTION,
                "generator_function_declaration": SymbolKind.FUNCTION,
                "class_declaration": SymbolKind.CLASS,
                "method_definition": SymbolKind.METHOD,
                "interface_declaration": SymbolKind.INTERFACE,
            },
            "java": {
                "method_declaration": SymbolKind.METHOD,
                "class_declaration": SymbolKind.CLASS,
                "interface_declaration": SymbolKind.INTERFACE,
                "enum_declaration": SymbolKind.ENUM,
                "record_declaration": SymbolKind.CLASS,
                "annotation_type_declaration": SymbolKind.INTERFACE,
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
                "module": SymbolKind.CLASS,
            },
            "swift": {
                "function_declaration": SymbolKind.FUNCTION,
                "class_declaration": SymbolKind.CLASS,
                "struct_declaration": SymbolKind.STRUCT,
                "protocol_declaration": SymbolKind.INTERFACE,
                "enum_declaration": SymbolKind.ENUM,
                "typealias_declaration": SymbolKind.TYPE_ALIAS,
            },
            "bash": {
                "function_definition": SymbolKind.FUNCTION,
            },
            "sql": {
                "create_table": SymbolKind.CLASS,
                "create_function": SymbolKind.FUNCTION,
            },
        }.get(language, {})
        symbols: list[SymbolDTO] = []
        nodes: dict[str, Node] = {}
        for node in self._walk(root):
            kind = mapping.get(node.type)
            if kind is None:
                continue
            name_node = node.child_by_field_name("name")
            boundary = self._definition_boundary(node)
            if name_node is None and boundary is not node:
                inner = self._definition_node(boundary)
                name_node = inner.child_by_field_name("name") if inner else None
            node = boundary
            name = self._valid_name(name_node, source, node, language)
            if len(name) > 255:
                continue
            if name.startswith("<anonymous:") and name_node is not None:
                # The name node exists but the name was rejected as a
                # keyword.  Skip this symbol entirely — an anonymous
                # placeholder from a keyword would be a false positive.
                continue
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

    @staticmethod
    def _definition_boundary(node: Node) -> Node:
        """Return the full source range for decorated definitions.

        Python represents decorators in an enclosing ``decorated_definition``
        node while the function/class name lives in the nested definition.
        Using the wrapper as the symbol boundary keeps ``@router.get(...)``
        attached to the route implementation and also works for decorated
        classes and methods.
        """
        parent = node.parent
        while parent is not None and parent.type == "decorated_definition":
            return parent
        return node

    @staticmethod
    def _definition_node(node: Node) -> Node | None:
        if node.type != "decorated_definition":
            return node
        for child in node.children:
            if child.type in {"function_definition", "class_definition"}:
                return child
        return None

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
        # Was O(n^2): every symbol rescanned the full symbol list to find its
        # smallest enclosing range. Symbol ranges from an AST nest properly
        # (no partial overlaps), so a single pass with a stack of currently
        # "open" ranges finds the nearest enclosing symbol in O(n) — the
        # stack top, after popping ranges that have already closed, is
        # always that nearest ancestor.
        symbols.sort(
            key=lambda item: (item.start_byte, -(item.end_byte - item.start_byte))
        )
        stack: list[SymbolDTO] = []
        for symbol in symbols:
            while stack and stack[-1].end_byte <= symbol.start_byte:
                stack.pop()
            if stack:
                parent = stack[-1]
                symbol.parent_symbol_id = parent.symbol_id
                symbol.parent_name = parent.name
                symbol.qualified_name = f"{parent.qualified_name}.{symbol.name}"
            stack.append(symbol)

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
        # Recursive `yield from` delegation re-enters every generator frame
        # on the call stack for each node yielded, which is O(depth) per
        # node (O(N * depth) overall) — costly on deeply nested ASTs. An
        # explicit stack keeps traversal O(N).
        stack = [node]
        while stack:
            current = stack.pop()
            yield current
            stack.extend(reversed(current.children))

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
    def _is_descendant_of(node: Node, ancestor: Node) -> bool:
        """True when *node* is strictly inside *ancestor*'s byte range."""
        return (
            node.start_byte >= ancestor.start_byte
            and node.end_byte <= ancestor.end_byte
        )

    @classmethod
    def _is_invalid_name(cls, name: str, language: str | None = None) -> bool:
        """Reject names that are keywords, empty, or look like operators."""
        if not name or not name.strip():
            return True
        if name in cls._KEYWORDS:
            return True
        if language is not None:
            lang_keywords = cls._LANGUAGE_KEYWORDS.get(language.lower())
            if lang_keywords is not None and name in lang_keywords:
                return True
        # Reject names that are purely operators or punctuation.
        if all(
            ch in "(){}[]<>+-*/%=!&|^~?:;,.#@\\\"'` \t\n\r"
            for ch in name
        ):
            return True
        return False

    @staticmethod
    def _split_import_clause(clause: str) -> list[str]:
        """Split a JS/TS import clause into individual imported names.

        ``import { foo, bar as baz }`` → ``['foo', 'bar']``
        ``import defaultExport, { named }`` → ``['defaultExport', 'named']``
        ``import * as ns`` → ``['*']``
        ``import type { Foo }`` → ``['Foo']``
        """
        clause = re.sub(r"\btype\s+", "", clause).strip()
        # Namespace import: import * as ns
        if clause.startswith("*"):
            return ["*"]
        parts: list[str] = []
        # Strip leading { and trailing }
        clause = clause.strip()
        if clause.startswith("{"):
            clause = clause[1:]
        if clause.endswith("}"):
            clause = clause[:-1]
        # Split by comma, but be careful with nested generics
        depth = 0
        current: list[str] = []
        for ch in clause:
            if ch in "<({":
                depth += 1
            elif ch in ">)}":
                depth -= 1
            elif ch == "," and depth == 0:
                parts.append("".join(current).strip())
                current = []
                continue
            current.append(ch)
        if current:
            parts.append("".join(current).strip())
        return [p for p in parts if p]

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

    def _valid_name(
        self, name_node: Node | None, source: bytes, node: Node,
        language: str | None = None,
    ) -> str:
        """Return the symbol name or an anonymous placeholder.

        Rejects keywords and empty names so that return/if/const/etc. never
        appear as extracted symbol names.
        """
        if name_node is not None:
            text = self._text(name_node, source)
            if text and not self._is_invalid_name(text, language):
                return text
        return self._anonymous_name(node)

    def _signature(self, node: Node, source: bytes) -> str:
        signature_node = self._definition_node(node) or node
        text = self._text(signature_node, source).splitlines()[0].strip()
        return text[:500]

    def _docstring(self, node: Node, source: bytes) -> str | None:
        node = self._definition_node(node) or node
        for child in node.children:
            if child.type in {"block", "class_body"}:
                for nested in child.children:
                    if nested.type in {"expression_statement"}:
                        # Expression statement as docstring: only accept
                        # string literals (triple-quoted or single-quoted),
                        # not arbitrary expressions or comments.
                        inner = (
                            nested.children[0] if nested.children else None
                        )
                        if inner is not None and inner.type == "string":
                            value = self._text(inner, source).strip()
                            if value:
                                return value
                        # Only check the first child; subsequent
                        # statements are body, not documentation.
                        break
                    if nested.type == "string":
                        value = self._text(nested, source).strip()
                        if value:
                            return value
                        break
                    if nested.type == "comment":
                        # Only accept doc-comment styles (///, //!, /**,
                        # ##, --[[, etc.), not ordinary // or # comments.
                        value = self._text(nested, source).strip()
                        if self._is_doc_comment(value):
                            return value
                        break
        return None

    @staticmethod
    def _is_doc_comment(text: str) -> bool:
        """True when a comment looks like documentation, not code narration."""
        if not text:
            return False
        return (
            text.startswith("/**")
            or text.startswith("///")
            or text.startswith("//!")
            or text.startswith("##")
            or text.startswith("--[[")
            or text.startswith("--[=[")
            or text.startswith('"""')
            or text.startswith("'''")
            or text.startswith("(*")
        )
