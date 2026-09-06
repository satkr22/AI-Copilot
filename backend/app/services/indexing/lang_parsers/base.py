from abc import ABC, abstractmethod

from tree_sitter import Tree

from app.services.indexing.dto import ParseResult


class BaseLanguageParser(ABC):

    @abstractmethod
    def extract(self, tree: Tree, source: bytes) -> ParseResult:
        pass