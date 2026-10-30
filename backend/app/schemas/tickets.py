from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.enums import AiDraftStatus, LabelSource, TicketCategory, TicketPriority, TicketStatus
from app.schemas.auth import UserOut
from app.schemas.books import BookOut


class TicketCreate(BaseModel):
    book_id: int | None = None
    subject: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=10, max_length=8000)
    attachment_names: list[str] = Field(default_factory=list, max_length=5)


class TicketPatch(BaseModel):
    status: TicketStatus | None = None
    category: TicketCategory | None = None
    priority: TicketPriority | None = None
    assigned_to_id: int | None = None


class MessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=8000)


class NoteCreate(BaseModel):
    body: str = Field(min_length=1, max_length=8000)


class MessageOut(BaseModel):
    id: int
    sender_id: int
    sender_name: str
    sender_role: str
    body: str
    created_at: datetime

    model_config = {"from_attributes": True}


class NoteOut(BaseModel):
    id: int
    admin_id: int
    admin_name: str
    body: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TicketSummary(BaseModel):
    id: int
    ticket_number: str
    subject: str
    status: TicketStatus
    category: TicketCategory
    category_source: LabelSource
    priority: TicketPriority
    priority_source: LabelSource
    priority_score: int
    book_id: int | None
    book_title: str | None
    author_id: int
    author_name: str
    assigned_to_id: int | None
    assigned_to_name: str | None
    ai_draft_status: AiDraftStatus
    created_at: datetime
    updated_at: datetime
    aging_hours: float

    model_config = {"from_attributes": True}


class TicketDetail(TicketSummary):
    description: str
    ai_draft: str | None
    ai_rationale: str | None
    ai_confidence: float | None
    book: BookOut | None = None
    author: UserOut | None = None
    messages: list[MessageOut] = Field(default_factory=list)
    notes: list[NoteOut] = Field(default_factory=list)


class AdminStats(BaseModel):
    open: int
    in_progress: int
    resolved: int
    closed: int
    critical: int
    high: int
    aging_over_48h: int


class QueueScope(BaseModel):
    status: TicketStatus | None = None
    category: TicketCategory | None = None
    priority: TicketPriority | None = None
    q: str | None = None
    sort: Literal["urgency", "newest"] = "urgency"
