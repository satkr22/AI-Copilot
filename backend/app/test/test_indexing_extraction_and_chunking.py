from app.services.indexing.chunking.cast_chunker import CastChunker
from app.services.indexing.extraction.query_extractor import QueryExtractor
from app.services.indexing.parser.parser_service import ParserService


def _extract(source: str):
    parsed = ParserService().parse_tree("python", source)
    return QueryExtractor().extract(
        parsed.tree,
        parsed.source_bytes,
        "app/api/routes/users.py",
        "python",
        parsed.language,
    )


def test_python_decorators_are_part_of_symbol_and_chunk():
    raw = _extract(
        "from fastapi import APIRouter\n"
        "router = APIRouter()\n\n"
        "@router.get(\"/users/{user_id}\", response_model=User)\n"
        "async def get_user(user_id: int):\n"
        "    \"\"\"Return one user.\"\"\"\n"
        "    return user_id\n"
    )

    symbol = next(item for item in raw.symbols if item.name == "get_user")
    source = raw.source_bytes[symbol.start_byte : symbol.end_byte].decode()
    assert source.startswith("@router.get")

    chunk = next(item for item in CastChunker().chunk(raw) if "get_user" in item.symbol_names)
    assert chunk.enriched_content is not None
    assert "@router.get" in chunk.content
    assert "# Entity: get_user" in chunk.enriched_content
    assert "# Documentation: Return one user." in chunk.enriched_content


def test_python_class_methods_and_decorated_classes_are_not_lost():
    raw = _extract(
        "@service\n"
        "class UserService:\n"
        "    @staticmethod\n"
        "    def get_user():\n"
        "        return None\n"
    )

    names = {item.name for item in raw.symbols}
    assert {"UserService", "get_user"}.issubset(names)
    method = next(item for item in raw.symbols if item.name == "get_user")
    assert method.parent_name == "UserService"


def test_merged_chunks_keep_entity_context():
    raw = _extract(
        "def first():\n"
        "    return 1\n\n"
        "def second():\n"
        "    return 2\n"
    )

    chunks = CastChunker(max_chunk_tokens=800).chunk(raw)
    merged = next(item for item in chunks if item.origin.value == "merged")
    assert merged.enriched_content is not None
    assert "# Entities:" in merged.enriched_content
    assert "first" in merged.enriched_content
    assert "second" in merged.enriched_content


def test_tsx_uses_tsx_grammar_for_jsx_components():
    source = (
        'import React from "react";\n'
        "export default function App() {\n"
        "  return (<main><h1>Hello</h1></main>);\n"
        "}\n"
    )
    parsed = ParserService().parse_tree(
        "typescript",
        source,
        grammar_language="tsx",
    )
    raw = QueryExtractor().extract(
        parsed.tree,
        parsed.source_bytes,
        "frontend/src/App.tsx",
        "typescript",
        parsed.language,
    )

    app = next(item for item in raw.symbols if item.name == "App")
    assert app.kind.value == "function"
    assert "<main>" in raw.source_bytes[app.start_byte : app.end_byte].decode()
