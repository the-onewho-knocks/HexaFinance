from pathlib import Path

from loguru import logger


def load_pdf_text(file_path: str | Path) -> str:
    path = Path(file_path)
    if not path.exists():
        logger.warning(f"PDF not found: {path}")
        return ""

    text_parts: list[str] = []

    try:
        import pypdf
        reader = pypdf.PdfReader(str(path))
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    except Exception as exc:
        logger.warning(f"pypdf failed for {path}: {exc}")

    if not text_parts:
        try:
            import pdfplumber
            with pdfplumber.open(str(path)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
        except Exception as exc:
            logger.warning(f"pdfplumber failed for {path}: {exc}")

    result = "\n\n".join(text_parts)
    logger.info(f"Extracted {len(result)} characters from {path.name}")
    return result


async def load_and_chunk_pdf(
    file_path: str | Path,
    symbol: str,
    form_type: str = "10-K",
) -> list[str]:
    text = load_pdf_text(file_path)
    if not text:
        return []

    from rag.ingestion.chunker import chunk_text
    return chunk_text(text)