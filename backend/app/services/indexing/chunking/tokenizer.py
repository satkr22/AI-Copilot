from __future__ import annotations

import math
from re import finditer


class CodeTokenCounter:
    """Count code tokens using the embedding tokenizer when it is available.

    ``cl100k_base`` is used because it is the tokenizer used by the OpenAI
    embedding models currently supported by this project.  The fallback is
    deliberately conservative: it estimates roughly one token per three
    UTF-8 bytes instead of pretending that whitespace-delimited words are
    model tokens.
    """

    def __init__(self, encoding_name: str = "cl100k_base") -> None:
        self._encoding = None
        try:
            import tiktoken

            self._encoding = tiktoken.get_encoding(encoding_name)
        except (ImportError, ValueError):
            # The requirements install tiktoken in normal deployments.  Keep
            # a usable conservative estimator for lightweight local tooling.
            self._encoding = None

    def count(self, text: str) -> int:
        if not text:
            return 0
        if self._encoding is not None:
            return len(self._encoding.encode(text, disallowed_special=()))

        byte_count = len(text.encode("utf-8"))
        lexical_tokens = sum(1 for _ in finditer(r"\w+|[^\w\s]", text))
        return max(1, lexical_tokens, math.ceil(byte_count / 3))
