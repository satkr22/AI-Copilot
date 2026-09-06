from tree_sitter import Parser
from tree_sitter_language_pack import get_language
from app.services.indexing.lang_parsers.python_parser import PythonParser
from app.services.indexing.lang_parsers.ts_parser import TypeScriptParser
from app.services.indexing.dto import ParseResult

class ParserService:

    def __init__(self):
        self.parsers = {}

        for lang in [
            "python",
            "typescript",
            "javascript",
            "java",
            "c",
        ]:
            parser = Parser()
            parser.language = get_language(lang) # type: ignore
            self.parsers[lang] = parser
        
        self.extractors = {
            "python": PythonParser(),
            "typescript": TypeScriptParser(),
            "javascript": TypeScriptParser(),
        }
    
    
    def parse(self, language: str, source: str) -> ParseResult:

        parser = self.parsers.get(language)

        if parser is None:
            raise ValueError(f"Unsupported language: {language}")

        source_bytes = source.encode("utf-8")
        
        tree = parser.parse(source_bytes)

        extractor = self.extractors[language]
        if extractor is None:
            raise NotImplementedError(
                f"No extractor implemented for {language}"
            )

        return extractor.extract(tree, source_bytes)
        