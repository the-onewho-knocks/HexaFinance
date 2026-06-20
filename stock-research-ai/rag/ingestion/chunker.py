
def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[str]:
    if not text:
        return []

    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk:
            chunks.append(chunk.strip())
        start += chunk_size - overlap

    return chunks


def chunk_document_by_sections(text: str) -> list[dict]:
    """Split text by common section headings and return chunks with metadata."""
    import re

    sections = re.split(r"\n(?=[A-Z][A-Z\s]{2,})", text)
    chunks: list[dict] = []

    for section in sections:
        lines = section.strip().split("\n", 1)
        heading = lines[0].strip() if len(lines) > 1 else ""
        body = lines[-1].strip() if lines else ""

        if len(body) < 50:
            continue

        sub_chunks = chunk_text(body)
        for i, sub in enumerate(sub_chunks):
            chunks.append({
                "heading": heading,
                "text": sub,
                "chunk_index": i,
            })

    return chunks