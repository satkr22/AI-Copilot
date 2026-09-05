from tree_sitter import Tree

from app.services.indexing.dto import ParseResult
from app.services.indexing.parsers.base import BaseLanguageParser


class TypeScriptParser(BaseLanguageParser):
    def extract(self, tree: Tree, source: bytes):
        return ParseResult([], [])