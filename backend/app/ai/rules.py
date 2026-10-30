from app.enums import PRIORITY_WEIGHT, TicketCategory, TicketPriority

_ROYALTY = ("royalty", "payout", "payment", "bank", "₹", "rupee", "threshold")
_ISBN = ("isbn", "metadata", "imprint", "wrong book")
_PRINT = ("print", "blurry", "binding", "misprint", "reprint", "quality", "pages", "color")
_DIST = ("unavailable", "out of stock", "currently unavailable", "re-sync", "resync", "not listed")
_GENERAL = ("author bio", "update my bio", "book description", "can i update", "bio")
_STATUS = ("typesetting", "cover design", "production", "proofread", "when will", "timeline", "stage")


def classify_ticket(subject: str, description: str) -> tuple[TicketCategory, TicketPriority, int, str]:
    text = f"{subject} {description}".lower()
    category = TicketCategory.GENERAL
    rationale = "No strong keyword match; defaulted to general inquiry."

    if any(token in text for token in _ROYALTY):
        category = TicketCategory.ROYALTY_PAYMENTS
        rationale = "Query mentions royalties or payouts."
    elif any(token in text for token in _ISBN):
        category = TicketCategory.ISBN_METADATA
        rationale = "Query mentions ISBN or metadata."
    elif any(token in text for token in _PRINT):
        category = TicketCategory.PRINTING_QUALITY
        rationale = "Query mentions print or quality defects."
    elif any(token in text for token in _DIST) or (
        ("amazon" in text or "flipkart" in text) and ("stock" in text or "listing" in text)
    ):
        category = TicketCategory.DISTRIBUTION
        rationale = "Query mentions store listing or availability."
    elif any(token in text for token in _GENERAL):
        category = TicketCategory.GENERAL
        rationale = "Query is a profile or metadata update request."
    elif any(token in text for token in _STATUS):
        category = TicketCategory.BOOK_STATUS
        rationale = "Query mentions production status or timeline."

    priority = TicketPriority.MEDIUM
    if any(token in text for token in ("6 months", "haven't received", "have not received", "never received", "overdue")):
        priority = TicketPriority.CRITICAL
        rationale += " Flagged critical because payment looks overdue."
    elif category == TicketCategory.ISBN_METADATA or any(token in text for token in ("terrible", "defective", "wrong isbn")):
        priority = TicketPriority.HIGH
        rationale += " Flagged high because ISBN or quality issues need fast escalation."
    elif any(token in text for token in ("bio", "description", "can i update")):
        priority = TicketPriority.LOW
        rationale += " Flagged low as a metadata or profile request."

    return category, priority, PRIORITY_WEIGHT[priority], rationale.strip()
