from abc import ABC, abstractmethod

from app.services.indexing.intelligence.models import (
    SymbolDTO,
    ImportDTO,
    CodeChunkDTO,
)


class CodeIntelligenceProvider(ABC):
    """
    Provider-independent semantic code intelligence interface.

    Implementations:
        - JCodeProvider
        - SymLensProvider
    """

    @abstractmethod
    def supports(self, language: str) -> bool:
        """
        Return True if this provider supports the given language.
        """
        raise NotImplementedError

    @abstractmethod
    def extract_symbols(
        self,
        source_code: str,
        language: str,
    ) -> list[SymbolDTO]:
        """
        Extract semantic symbols from source code.
        """
        raise NotImplementedError

    @abstractmethod
    def extract_imports(
        self,
        source_code: str,
        language: str,
    ) -> list[ImportDTO]:
        """
        Extract import statements from source code.
        """
        raise NotImplementedError

    @abstractmethod
    def create_chunks(
        self,
        source_code: str,
        language: str,
        symbols: list[SymbolDTO],
    ) -> list[CodeChunkDTO]:
        """
        Generate semantic code chunks using the extracted symbols.
        """
        raise NotImplementedError