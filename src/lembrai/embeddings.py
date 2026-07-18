from collections.abc import Callable

Embedder = Callable[[list[str]], list[list[float]]]

EMBEDDING_MODEL = "intfloat/multilingual-e5-small"

# e5 models are trained with these prefixes; skipping them degrades retrieval
QUERY_PREFIX = "query: "
PASSAGE_PREFIX = "passage: "


def create_embedder() -> Embedder:
    # deferred import: sentence-transformers pulls torch, which tests never need
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(EMBEDDING_MODEL)

    def embed(texts: list[str]) -> list[list[float]]:
        return model.encode(texts, normalize_embeddings=True).tolist()

    return embed
