from collections.abc import Callable
from dataclasses import dataclass

EMBEDDING_MODEL = "intfloat/multilingual-e5-small"

# e5 models are trained with these prefixes; skipping them degrades retrieval
_QUERY_PREFIX = "query: "
_PASSAGE_PREFIX = "passage: "

EmbedTexts = Callable[[list[str]], list[list[float]]]


@dataclass(frozen=True)
class Embedder:
    embed_queries: EmbedTexts
    embed_passages: EmbedTexts


def create_embedder() -> Embedder:
    # deferred import: sentence-transformers pulls torch, which tests never need
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(EMBEDDING_MODEL)

    def embed_with_prefix(prefix: str, texts: list[str]) -> list[list[float]]:
        prefixed = [prefix + text for text in texts]
        return model.encode(prefixed, normalize_embeddings=True).tolist()

    return Embedder(
        embed_queries=lambda texts: embed_with_prefix(_QUERY_PREFIX, texts),
        embed_passages=lambda texts: embed_with_prefix(_PASSAGE_PREFIX, texts),
    )
