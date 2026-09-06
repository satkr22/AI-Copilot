from app.services.indexing.intelligence.interface import CodeIntelligenceProvider, CodeChunkDTO
from app.services.indexing.intelligence.models import ImportDTO, ParseResultDTO, SymbolDTO, SymbolKind, ChunkType

class JCodeProvider(CodeIntelligenceProvider):
    
    def supports(self, language: str) -> bool:
        return language == "python"
    
    
    def extract_symbols(
        self,
        source_code: str,
        language: str,
    ) -> list[SymbolDTO]:
        
        symbols = []
        return symbols
    
    
    def extract_imports(
        self,
        source_code: str,
        language: str,
    ) -> list[ImportDTO]:
        
        imprts = []
        return imprts

    def create_chunks(
        self,
        source_code: str,
        language: str,
        symbols: list[SymbolDTO],
    ) -> list[CodeChunkDTO]:
        
        chunks = []
        return chunks