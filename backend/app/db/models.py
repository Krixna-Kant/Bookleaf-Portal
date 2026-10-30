from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.enums import AiDraftStatus, LabelSource, TicketCategory, TicketEventType, TicketPriority, TicketStatus, UserRole


def _enum_values(enum_cls):
    return [item.value for item in enum_cls]


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role", values_callable=_enum_values), nullable=False)
    external_author_id: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    joined_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    books: Mapped[list["Book"]] = relationship(back_populates="author")
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="author", foreign_keys="Ticket.author_id")
    assigned_tickets: Mapped[list["Ticket"]] = relationship(back_populates="assignee", foreign_keys="Ticket.assigned_to_id")


class Book(TimestampMixin, Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_book_id: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    isbn: Mapped[str | None] = mapped_column(String(64), nullable=True)
    genre: Mapped[str | None] = mapped_column(String(128), nullable=True)
    publication_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(128), nullable=False)
    mrp: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    author_royalty_per_copy: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    total_copies_sold: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_royalty_earned: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    royalty_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    royalty_pending: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    last_royalty_payout_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    print_partner: Mapped[str | None] = mapped_column(String(128), nullable=True)

    author: Mapped[User] = relationship(back_populates="books")
    platforms: Mapped[list["BookPlatform"]] = relationship(back_populates="book", cascade="all, delete-orphan")
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="book")


class BookPlatform(Base):
    __tablename__ = "book_platforms"
    __table_args__ = (UniqueConstraint("book_id", "platform", name="uq_book_platform"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), index=True, nullable=False)
    platform: Mapped[str] = mapped_column(String(128), nullable=False)

    book: Mapped[Book] = relationship(back_populates="platforms")


class Ticket(TimestampMixin, Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_number: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    book_id: Mapped[int | None] = mapped_column(ForeignKey("books.id", ondelete="SET NULL"), nullable=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[TicketCategory] = mapped_column(
        Enum(TicketCategory, name="ticket_category", values_callable=_enum_values), nullable=False
    )
    category_source: Mapped[LabelSource] = mapped_column(
        Enum(LabelSource, name="label_source", values_callable=_enum_values), nullable=False
    )
    ai_confidence: Mapped[float | None] = mapped_column(nullable=True)
    priority: Mapped[TicketPriority] = mapped_column(
        Enum(TicketPriority, name="ticket_priority", values_callable=_enum_values), nullable=False
    )
    priority_source: Mapped[LabelSource] = mapped_column(
        Enum(LabelSource, name="label_source", values_callable=_enum_values), nullable=False
    )
    priority_score: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus, name="ticket_status", values_callable=_enum_values),
        default=TicketStatus.OPEN,
        index=True,
        nullable=False,
    )
    assigned_to_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    ai_draft: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_draft_status: Mapped[AiDraftStatus] = mapped_column(
        Enum(AiDraftStatus, name="ai_draft_status", values_callable=_enum_values),
        default=AiDraftStatus.PENDING,
        nullable=False,
    )
    ai_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    author: Mapped[User] = relationship(back_populates="tickets", foreign_keys=[author_id])
    book: Mapped[Book | None] = relationship(back_populates="tickets")
    assignee: Mapped[User | None] = relationship(back_populates="assigned_tickets", foreign_keys=[assigned_to_id])
    messages: Mapped[list["TicketMessage"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan", order_by="TicketMessage.created_at"
    )
    notes: Mapped[list["TicketNote"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan", order_by="TicketNote.created_at"
    )
    events: Mapped[list["TicketEvent"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan", order_by="TicketEvent.created_at"
    )


class TicketMessage(Base):
    __tablename__ = "ticket_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"), index=True, nullable=False)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    ticket: Mapped[Ticket] = relationship(back_populates="messages")
    sender: Mapped[User] = relationship()


class TicketNote(Base):
    __tablename__ = "ticket_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"), index=True, nullable=False)
    admin_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    ticket: Mapped[Ticket] = relationship(back_populates="notes")
    admin: Mapped[User] = relationship()


class TicketEvent(Base):
    __tablename__ = "ticket_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"), index=True, nullable=False)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    event_type: Mapped[TicketEventType] = mapped_column(
        Enum(TicketEventType, name="ticket_event_type", values_callable=_enum_values), nullable=False
    )
    payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    ticket: Mapped[Ticket] = relationship(back_populates="events")
    actor: Mapped[User | None] = relationship()
