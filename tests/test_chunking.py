from lembrai.chunking import chunk_text


def test_empty_text_yields_no_chunks():
    assert chunk_text("   \n\n  ") == []


def test_short_text_is_a_single_chunk():
    assert chunk_text("uma nota curta") == ["uma nota curta"]


def test_paragraphs_are_packed_up_to_the_limit():
    assert chunk_text("aaa\n\nbbb\n\nccc", max_chars=8) == ["aaa\n\nbbb", "ccc"]


def test_oversized_paragraph_is_kept_whole():
    text = "x" * 50 + "\n\n" + "yy"
    assert chunk_text(text, max_chars=10) == ["x" * 50, "yy"]
