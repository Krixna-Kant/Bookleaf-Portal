"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

user_role = postgresql.ENUM("author", "admin", name="user_role", create_type=False)
ticket_category = postgresql.ENUM(
    "royalty_payments",
    "isbn_metadata",
    "printing_quality",
    "distribution",
    "book_status",
    "general",
    name="ticket_category",
    create_type=False,
)
label_source = postgresql.ENUM("ai", "admin", "rule", name="label_source", create_type=False)
ticket_priority = postgresql.ENUM("critical", "high", "medium", "low", name="ticket_priority", create_type=False)
ticket_status = postgresql.ENUM("open", "in_progress", "resolved", "closed", name="ticket_status", create_type=False)
ai_draft_status = postgresql.ENUM("pending", "ready", "failed", "sent", name="ai_draft_status", create_type=False)
ticket_event_type = postgresql.ENUM(
    "ticket.created",
    "ticket.classified",
    "ticket.drafted",
    "ticket.updated",
    "ticket.assigned",
    "ticket.note_added",
    "ticket.replied",
    name="ticket_event_type",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    user_role.create(bind, checkfirst=True)
    ticket_category.create(bind, checkfirst=True)
    label_source.create(bind, checkfirst=True)
    ticket_priority.create(bind, checkfirst=True)
    ticket_status.create(bind, checkfirst=True)
    ai_draft_status.create(bind, checkfirst=True)
    ticket_event_type.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("external_author_id", sa.String(32), nullable=True),
        sa.Column("phone", sa.String(64), nullable=True),
        sa.Column("city", sa.String(128), nullable=True),
        sa.Column("joined_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_external_author_id", "users", ["external_author_id"], unique=True)

    op.create_table(
        "books",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("external_book_id", sa.String(32), nullable=False),
        sa.Column("author_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("isbn", sa.String(64), nullable=True),
        sa.Column("genre", sa.String(128), nullable=True),
        sa.Column("publication_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(128), nullable=False),
        sa.Column("mrp", sa.Numeric(12, 2), nullable=True),
        sa.Column("author_royalty_per_copy", sa.Numeric(12, 2), nullable=True),
        sa.Column("total_copies_sold", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_royalty_earned", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("royalty_paid", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("royalty_pending", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("last_royalty_payout_date", sa.Date(), nullable=True),
        sa.Column("print_partner", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_books_external_book_id", "books", ["external_book_id"], unique=True)
    op.create_index("ix_books_author_id", "books", ["author_id"])

    op.create_table(
        "book_platforms",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("book_id", sa.Integer(), sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False),
        sa.Column("platform", sa.String(128), nullable=False),
        sa.UniqueConstraint("book_id", "platform", name="uq_book_platform"),
    )
    op.create_index("ix_book_platforms_book_id", "book_platforms", ["book_id"])

    op.create_table(
        "tickets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticket_number", sa.String(32), nullable=False),
        sa.Column("author_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("book_id", sa.Integer(), sa.ForeignKey("books.id", ondelete="SET NULL"), nullable=True),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", ticket_category, nullable=False),
        sa.Column("category_source", label_source, nullable=False),
        sa.Column("ai_confidence", sa.Float(), nullable=True),
        sa.Column("priority", ticket_priority, nullable=False),
        sa.Column("priority_source", label_source, nullable=False),
        sa.Column("priority_score", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("status", ticket_status, nullable=False, server_default="open"),
        sa.Column("assigned_to_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("ai_draft", sa.Text(), nullable=True),
        sa.Column("ai_draft_status", ai_draft_status, nullable=False, server_default="pending"),
        sa.Column("ai_rationale", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_tickets_ticket_number", "tickets", ["ticket_number"], unique=True)
    op.create_index("ix_tickets_author_id", "tickets", ["author_id"])
    op.create_index("ix_tickets_status", "tickets", ["status"])
    op.create_index("ix_tickets_priority_created", "tickets", ["priority", "created_at"])

    op.create_table(
        "ticket_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticket_id", sa.Integer(), sa.ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sender_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ticket_messages_ticket_id", "ticket_messages", ["ticket_id"])

    op.create_table(
        "ticket_notes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticket_id", sa.Integer(), sa.ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("admin_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ticket_notes_ticket_id", "ticket_notes", ["ticket_id"])

    op.create_table(
        "ticket_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticket_id", sa.Integer(), sa.ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("event_type", ticket_event_type, nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ticket_events_ticket_id", "ticket_events", ["ticket_id"])


def downgrade() -> None:
    op.drop_table("ticket_events")
    op.drop_table("ticket_notes")
    op.drop_table("ticket_messages")
    op.drop_table("tickets")
    op.drop_table("book_platforms")
    op.drop_table("books")
    op.drop_table("users")
    ticket_event_type.drop(op.get_bind(), checkfirst=True)
    ai_draft_status.drop(op.get_bind(), checkfirst=True)
    ticket_status.drop(op.get_bind(), checkfirst=True)
    ticket_priority.drop(op.get_bind(), checkfirst=True)
    label_source.drop(op.get_bind(), checkfirst=True)
    ticket_category.drop(op.get_bind(), checkfirst=True)
    user_role.drop(op.get_bind(), checkfirst=True)
