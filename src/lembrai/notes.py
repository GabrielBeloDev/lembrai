from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import chromadb

from lembrai.chunking import chunk_text
from lembrai.embeddings import PASSAGE_PREFIX, QUERY_PREFIX, Embedder

NOTES_DIR = Path("data/notes")
CHROMA_DIR = Path("data/chroma")
COLLECTION_NAME = "notas"
TOP_K = 3


@dataclass(frozen=True)
class NoteMatch:
    text: str
    saved_at: str


def as_context(matches: list[NoteMatch]) -> str:
    lines = [f"- ({match.saved_at}) {match.text}" for match in matches]
    return (
        "Notas do usuário possivelmente relevantes para a mensagem atual "
        "(use apenas se ajudarem):\n" + "\n".join(lines)
    )


class NoteStore:
    def __init__(
        self,
        embed: Embedder,
        notes_dir: Path = NOTES_DIR,
        chroma_dir: Path = CHROMA_DIR,
    ):
        self._embed = embed
        self._notes_dir = notes_dir
        client = chromadb.PersistentClient(path=str(chroma_dir))
        self._collection = client.get_or_create_collection(COLLECTION_NAME)

    def add(self, text: str) -> Path:
        saved_at = datetime.now()
        note_id = saved_at.strftime("%Y%m%d-%H%M%S-%f")
        self._notes_dir.mkdir(parents=True, exist_ok=True)
        path = self._notes_dir / f"{note_id}.md"
        path.write_text(text + "\n", encoding="utf-8")
        chunks = chunk_text(text)
        self._collection.add(
            ids=[f"{note_id}-{position}" for position in range(len(chunks))],
            documents=chunks,
            embeddings=self._embed([PASSAGE_PREFIX + chunk for chunk in chunks]),
            metadatas=[
                {"saved_at": saved_at.isoformat(timespec="seconds")}
                for _ in chunks
            ],
        )
        return path

    def search(self, query: str, top_k: int = TOP_K) -> list[NoteMatch]:
        stored_chunks = self._collection.count()
        if stored_chunks == 0:
            return []
        result = self._collection.query(
            query_embeddings=self._embed([QUERY_PREFIX + query]),
            n_results=min(top_k, stored_chunks),
            include=["documents", "metadatas"],
        )
        documents = result["documents"][0]
        metadatas = result["metadatas"][0]
        return [
            NoteMatch(text=document, saved_at=str(metadata["saved_at"]))
            for document, metadata in zip(documents, metadatas)
        ]
