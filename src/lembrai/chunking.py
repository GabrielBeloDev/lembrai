MAX_CHUNK_CHARS = 800


def chunk_text(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
        # an oversized paragraph is kept whole: notes are short and splitting
        # mid-sentence hurts retrieval more than one long chunk
        current = paragraph
    if current:
        chunks.append(current)
    return chunks
