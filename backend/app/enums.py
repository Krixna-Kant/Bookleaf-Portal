from enum import Enum


class UserRole(str, Enum):
    AUTHOR = "author"
    ADMIN = "admin"


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketCategory(str, Enum):
    ROYALTY_PAYMENTS = "royalty_payments"
    ISBN_METADATA = "isbn_metadata"
    PRINTING_QUALITY = "printing_quality"
    DISTRIBUTION = "distribution"
    BOOK_STATUS = "book_status"
    GENERAL = "general"


class TicketPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class LabelSource(str, Enum):
    AI = "ai"
    ADMIN = "admin"
    RULE = "rule"


class AiDraftStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    FAILED = "failed"
    SENT = "sent"


class TicketEventType(str, Enum):
    CREATED = "ticket.created"
    CLASSIFIED = "ticket.classified"
    DRAFTED = "ticket.drafted"
    UPDATED = "ticket.updated"
    ASSIGNED = "ticket.assigned"
    NOTE_ADDED = "ticket.note_added"
    REPLIED = "ticket.replied"


CATEGORY_LABELS: dict[TicketCategory, str] = {
    TicketCategory.ROYALTY_PAYMENTS: "Royalty & Payments",
    TicketCategory.ISBN_METADATA: "ISBN & Metadata Issues",
    TicketCategory.PRINTING_QUALITY: "Printing & Quality",
    TicketCategory.DISTRIBUTION: "Distribution & Availability",
    TicketCategory.BOOK_STATUS: "Book Status & Production Updates",
    TicketCategory.GENERAL: "General Inquiry",
}

PRIORITY_WEIGHT: dict[TicketPriority, int] = {
    TicketPriority.CRITICAL: 100,
    TicketPriority.HIGH: 75,
    TicketPriority.MEDIUM: 50,
    TicketPriority.LOW: 25,
}

PAYOUT_THRESHOLD_INR = 1000
