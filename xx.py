from tree_sitter_language_pack import get_language

languages = [
    "python",
    "javascript",
    "typescript",
    "java",
    "cpp",
    "c",
    "rust",
    "go",
    "php",
    "perl",
    "swift",
    "csharp",
    "kotlin",
    "json",
    "bash",
    "markdown"
]

for lang in languages:
    py_language = get_language(lang) # type: ignore

    print(f"{lang.upper()} node kind count:", py_language.node_kind_count)