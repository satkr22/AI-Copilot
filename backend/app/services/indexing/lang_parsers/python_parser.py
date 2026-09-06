# from tree_sitter import Node, Tree

# from app.services.indexing.intelligence.models import ImportDTO, ParseResultDTO, SymbolDTO, SymbolKind, ChunkType
# from app.services.indexing.lang_parsers.base import BaseLanguageParser


# class PythonParser(BaseLanguageParser):
#     """
#     MVP Python extractor.

#     Extracts:
#     - class_definition
#     - function_definition (top-level)
#     - method_definition (function inside class)
#     - import_statement
#     - import_from_statement
#     """

#     def extract(self, tree: Tree, source: bytes) -> ParseResultDTO:
#         symbols: list[SymbolDTO] = []
#         imports: list[ImportDTO] = []

#         self._walk(
#             node=tree.root_node,
#             source=source,
#             symbols=symbols,
#             imports=imports,
#         )

#         return ParseResultDTO(
#             symbols=symbols,
#             imports=imports,
#             chunks=[]
#         )

#     def _walk(
#         self,
#         node: Node,
#         source: bytes,
#         symbols: list[SymbolDTO],
#         imports: list[ImportDTO],
#     ) -> None:
#         """
#         Depth-first traversal of the AST.
#         """

#         if node.type == "class_definition":
#             symbols.append(self._extract_class(node, source))

#         elif node.type == "function_definition":
#             symbols.append(self._extract_function_or_method(node, source))

#         elif node.type == "import_statement":
#             imports.extend(self._extract_import_statement(node, source))

#         elif node.type == "import_from_statement":
#             imports.extend(self._extract_import_from_statement(node, source))

#         for child in node.children:
#             self._walk(child, source, symbols, imports)

#     def _extract_class(self, node: Node, source: bytes) -> SymbolDTO:
#         name_node = node.child_by_field_name("name")

#         return SymbolDTO(
#             name=self._text(name_node, source),
#             kind=SymbolKind("class"),
#             language="python",
#             start_line=node.start_point[0] + 1,
#             end_line=node.end_point[0] + 1,
#         )

#     def _extract_function_or_method(
#         self,
#         node: Node,
#         source: bytes,
#     ) -> SymbolDTO:
#         name_node = node.child_by_field_name("name")

#         kind = (
#             "method"
#             if self._is_method(node)
#             else "function"
#         )

#         return SymbolDTO(
#             name=self._text(name_node, source),
#             kind=SymbolKind(kind),
#             language="python",
#             start_line=node.start_point[0] + 1,
#             end_line=node.end_point[0] + 1,
#         )

#     def _extract_import_statement(
#         self,
#         node: Node,
#         source: bytes,
#     ) -> list[ImportDTO]:
#         """
#         Handles:
#             import os
#             import json
#             import numpy as np
#         """

#         results: list[ImportDTO] = []

#         for child in node.children:
#             if child.type == "dotted_name":
#                 module = self._text(child, source)
#                 print(self._text(child, source))

#                 results.append(
#                     ImportDTO(
#                         import_path=module,
#                         import_name=module.split(".")[-1],
#                         language="python",
#                         line_number=node.start_point[0] + 1,
#                     )
#                 )

#             elif child.type == "aliased_import":
#                 name = child.child_by_field_name("name")
#                 module = self._text(name, source)

#                 results.append(
#                     ImportDTO(
#                         import_path=module,
#                         import_name=module.split(".")[-1],
#                         language="python",
#                         line_number=node.start_point[0] + 1,
#                     )
#                 )

#         return results

#     def _extract_import_from_statement(
#         self,
#         node: Node,
#         source: bytes,
#     ) -> list[ImportDTO]:

#         results: list[ImportDTO] = []

#         statement = self._text(node, source)
#         print(self._text(node, source))
#         line_number = node.start_point[0] + 1

#         # Split "from X import Y"
#         try:
#             from_part, import_part = statement.split(" import ", 1)
#         except ValueError:
#             return results

#         # Remove leading "from "
#         module = from_part[len("from "):].strip()

#         # Multiple imports: from x import a, b
#         for name in import_part.split(","):
#             imported = name.strip()

#             if not imported:
#                 continue

#             # Handle alias: "router as r"
#             if " as " in imported:
#                 imported = imported.split(" as ", 1)[0].strip()

#             results.append(
#                 ImportDTO(
#                     import_path=module,
#                     import_name=imported,
#                     language="python",
#                     line_number=line_number,
#                 )
#             )

#         return results

#     @staticmethod
#     def _is_method(node: Node) -> bool:
#         """
#         A method is:
#         class_definition
#             └── block
#                     └── function_definition
#         """

#         parent = node.parent

#         if parent is None or parent.type != "block":
#             return False

#         grandparent = parent.parent

#         return (
#             grandparent is not None
#             and grandparent.type == "class_definition"
#         )

#     @staticmethod
#     def _text(node: Node | None, source: bytes) -> str:
#         if node is None:
#             return ""

#         return source[node.start_byte : node.end_byte].decode("utf-8")