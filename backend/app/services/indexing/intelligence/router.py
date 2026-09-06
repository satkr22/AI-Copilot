from app.services.indexing.intelligence.interface import CodeIntelligenceProvider
from app.services.indexing.intelligence.providers.jcode_provider import JCodeProvider
from app.services.indexing.intelligence.providers.symlens_provider import SymLensProvider


class IntelligenceRouter:
    """
    Selects the appropriate semantic intelligence provider
    based on programming language.
    """

    SYMLENS_LANGUAGES = {
        "typescript",
        "javascript",
        "rust",
        "go",
        "java",
        "kotlin",
        "swift",
        "c",
        "cpp",
    }

    def __init__(self) -> None:
        self._providers: list[CodeIntelligenceProvider] = [
            JCodeProvider(),
            SymLensProvider(),
        ]

    def get_provider(self, language: str) -> CodeIntelligenceProvider | None:
        """
        Return the best provider for a language.

        Priority:
        Python      -> JCode
        Others      -> SymLens
        Unsupported -> skip file
        """
        language = language.lower()

        for provider in self._providers:
            if provider.supports(language):
                return provider

        return None