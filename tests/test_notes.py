from pathlib import Path

from lembrai.embeddings import Embedder
from lembrai.notes import NoteMatch, NoteStore, as_context


def keyword_vector(text: str) -> list[float]:
    return [1.0 if "café" in text else 0.0, 1.0 if "código" in text else 0.0]


FAKE_EMBEDDER = Embedder(
    embed_queries=lambda texts: [keyword_vector(text) for text in texts],
    embed_passages=lambda texts: [keyword_vector(text) for text in texts],
)


def make_store(tmp_path: Path) -> NoteStore:
    return NoteStore(
        embedder=FAKE_EMBEDDER,
        notes_dir=tmp_path / "notes",
        chroma_dir=tmp_path / "chroma",
    )


def test_add_writes_the_note_to_a_markdown_file(tmp_path: Path):
    store = make_store(tmp_path)
    path = store.add("tomei um café ótimo hoje")
    assert path.read_text(encoding="utf-8") == "tomei um café ótimo hoje\n"


def test_search_returns_the_closest_note_first(tmp_path: Path):
    store = make_store(tmp_path)
    store.add("tomei um café ótimo hoje")
    store.add("refatorei o código do projeto")
    matches = store.search("onde tomei café?", top_k=1)
    assert len(matches) == 1
    assert "café" in matches[0].text


def test_long_note_is_split_into_searchable_chunks(tmp_path: Path):
    store = make_store(tmp_path)
    coffee_paragraph = ("tomei um café ótimo com a equipe " * 20).strip()
    code_paragraph = ("refatorei o código do serviço " * 20).strip()
    store.add(f"{coffee_paragraph}\n\n{code_paragraph}")
    matches = store.search("onde tomei café?")
    assert len(matches) == 2
    assert "café" in matches[0].text
    assert "código" in matches[1].text


def test_search_on_an_empty_store_returns_nothing(tmp_path: Path):
    assert make_store(tmp_path).search("qualquer coisa") == []


def test_context_lists_every_note_with_its_date():
    matches = [
        NoteMatch(text="tomei café", saved_at="2026-07-18T10:00:00"),
        NoteMatch(text="refatorei o código", saved_at="2026-07-17T09:00:00"),
    ]
    context = as_context(matches)
    assert "tomei café" in context
    assert "refatorei o código" in context
    assert "2026-07-18" in context
    assert "2026-07-17" in context
