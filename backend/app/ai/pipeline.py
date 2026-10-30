from __future__ import annotations

import json
import logging
import re

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.ai.kb import draft_context, estimate_tokens
from app.ai.provider import LLMError, get_provider
from app.ai.rules import classify_ticket
from app.db.models import Book, Ticket, TicketEvent
from app.db.session import SessionLocal
from app.enums import (
    PRIORITY_WEIGHT,
    AiDraftStatus,
    LabelSource,
    TicketCategory,
    TicketEventType,
    TicketPriority,
)

logger = logging.getLogger(__name__)

CLASSIFY_SYSTEM = """You classify BookLeaf author support tickets.
Return ONLY compact JSON with keys:
category: one of royalty_payments, isbn_metadata, printing_quality, distribution, book_status, general
priority: one of critical, high, medium, low
confidence: number 0-1
rationale: one short sentence
Rules:
- Overdue or missing royalties for months = critical or high
- ISBN mismatch or wrong metadata = high
- Print defects = high
- Bio/description updates = low
Do not use the knowledge base. Use only the query and book snapshot."""

DRAFT_SYSTEM_PREFIX = """Write a reply an ops teammate can send after a quick edit.
Length: 120-180 words. No subject line. No bullet dump unless numbers need a list.
"""


def _book_snapshot(book: Book | None) -> str:
    if book is None:
        return "Book: General / account-level query (no specific title)."
    pending = float(book.royalty_pending)
    threshold = "below ₹1,000 payout threshold (rolls over)" if 0 < pending < 1000 else "meets or exceeds payout threshold"
    return (
        f"Book: {book.title} ({book.external_book_id})\n"
        f"Status: {book.status}\n"
        f"ISBN: {book.isbn or 'not assigned yet'}\n"
        f"MRP: {book.mrp if book.mrp is not None else 'n/a'}\n"
        f"Copies sold: {book.total_copies_sold}\n"
        f"Royalty earned/paid/pending: {book.total_royalty_earned}/{book.royalty_paid}/{book.royalty_pending}\n"
        f"Last payout: {book.last_royalty_payout_date or 'never'}\n"
        f"Payout note: {threshold}\n"
        f"Print partner: {book.print_partner or 'n/a'}\n"
        f"Platforms: {', '.join(p.platform for p in book.platforms) or 'none yet'}"
    )


def _parse_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, flags=re.S)
    if not match:
        raise ValueError("No JSON object in model output")
    return json.loads(match.group(0))


def run_ai_pipeline(ticket_id: int) -> None:
    db = SessionLocal()
    try:
        ticket = db.scalar(
            select(Ticket)
            .options(selectinload(Ticket.book).selectinload(Book.platforms), selectinload(Ticket.author))
            .where(Ticket.id == ticket_id)
        )
        if ticket is None:
            return

        provider = get_provider()
        if provider is None:
            ticket.ai_draft_status = AiDraftStatus.FAILED
            ticket.ai_rationale = (ticket.ai_rationale or "") + " LLM unavailable; rule-based labels kept."
            db.commit()
            return

        snapshot = _book_snapshot(ticket.book)
        query = f"Subject: {ticket.subject}\nDescription: {ticket.description}\nAuthor: {ticket.author.name}\n{snapshot}"

        try:
            classify_user = query + "\nReturn JSON only."
            logger.info(
                "AI classify tokens~%s provider=%s",
                estimate_tokens(CLASSIFY_SYSTEM, classify_user),
                provider.name,
            )
            raw = provider.complete(CLASSIFY_SYSTEM, classify_user)
            parsed = _parse_json(raw)
            category = TicketCategory(parsed["category"])
            priority = TicketPriority(parsed["priority"])
            ticket.category = category
            ticket.priority = priority
            ticket.priority_score = PRIORITY_WEIGHT[priority]
            ticket.category_source = LabelSource.AI
            ticket.priority_source = LabelSource.AI
            ticket.ai_confidence = float(parsed.get("confidence") or 0)
            ticket.ai_rationale = str(parsed.get("rationale") or "")
            db.add(
                TicketEvent(
                    ticket_id=ticket.id,
                    actor_id=None,
                    event_type=TicketEventType.CLASSIFIED,
                    payload={"provider": provider.name, "category": category.value, "priority": priority.value},
                )
            )
        except (LLMError, ValueError, KeyError) as exc:
            logger.warning("AI classify failed, keeping rules: %s", exc)
            category = ticket.category
            rule_cat, rule_pri, rule_score, rule_why = classify_ticket(ticket.subject, ticket.description)
            if ticket.category_source == LabelSource.RULE:
                ticket.category = rule_cat
                ticket.priority = rule_pri
                ticket.priority_score = rule_score
                ticket.ai_rationale = rule_why
                category = rule_cat

        kb, kb_tokens = draft_context(category)
        draft_system = DRAFT_SYSTEM_PREFIX + kb
        draft_user = (
            f"{query}\n\nWrite the author-facing reply now. Use the royalty and status numbers above."
        )
        logger.info("AI draft tokens~%s slice=%s", estimate_tokens(draft_system, draft_user) + kb_tokens, category.value)
        try:
            draft = provider.complete(draft_system, draft_user)
            ticket.ai_draft = draft
            ticket.ai_draft_status = AiDraftStatus.READY
            db.add(
                TicketEvent(
                    ticket_id=ticket.id,
                    actor_id=None,
                    event_type=TicketEventType.DRAFTED,
                    payload={"provider": provider.name},
                )
            )
        except LLMError as exc:
            logger.warning("AI draft failed: %s", exc)
            ticket.ai_draft_status = AiDraftStatus.FAILED
        db.commit()
    except Exception:
        logger.exception("AI pipeline crashed for ticket %s", ticket_id)
        db.rollback()
        ticket = db.get(Ticket, ticket_id)
        if ticket:
            ticket.ai_draft_status = AiDraftStatus.FAILED
            db.commit()
    finally:
        db.close()
