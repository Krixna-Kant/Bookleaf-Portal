from functools import lru_cache
from pathlib import Path

from app.enums import TicketCategory

KB_DIR = Path(__file__).resolve().parent / "kb"

CATEGORY_FILES = {
    TicketCategory.ROYALTY_PAYMENTS: "royalty_payments.md",
    TicketCategory.ISBN_METADATA: "isbn_metadata.md",
    TicketCategory.PRINTING_QUALITY: "printing_quality.md",
    TicketCategory.DISTRIBUTION: "distribution.md",
    TicketCategory.BOOK_STATUS: "book_status.md",
    TicketCategory.GENERAL: "general.md",
}


def _read(name: str) -> str:
    return (KB_DIR / name).read_text(encoding="utf-8").strip()


@lru_cache
def tone_guide() -> str:
    return _read("tone.md")


@lru_cache
def category_slice(category: TicketCategory) -> str:
    return _read(CATEGORY_FILES[category])


def estimate_tokens(*chunks: str) -> int:
    return max(1, sum(len(chunk) for chunk in chunks) // 4)


def draft_context(category: TicketCategory) -> tuple[str, int]:
    tone = tone_guide()
    slice_text = category_slice(category)
    tokens = estimate_tokens(tone, slice_text)
    return f"{tone}\n\n---\n\n{slice_text}", tokens
