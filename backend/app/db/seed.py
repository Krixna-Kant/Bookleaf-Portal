from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.models import Book, BookPlatform, Ticket, TicketEvent, TicketMessage, User
from app.db.session import SessionLocal
from app.enums import AiDraftStatus, LabelSource, TicketCategory, TicketEventType, TicketPriority, TicketStatus, UserRole

DATA_PATH = Path(__file__).resolve().parents[3] / "data" / "bookleaf_sample_data.json"


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def _money(value) -> Decimal:
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


def _optional_money(value) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def seed(db: Session) -> None:
    settings = get_settings()
    raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    author_password = hash_password(settings.seed_author_password)

    authors_by_external: dict[str, User] = {}
    books_by_external: dict[str, Book] = {}

    for author_data in raw["authors"]:
        existing = db.scalar(select(User).where(User.external_author_id == author_data["author_id"]))
        if existing:
            user = existing
        else:
            user = User(
                email=author_data["email"].lower(),
                password_hash=author_password,
                name=author_data["name"],
                role=UserRole.AUTHOR,
                external_author_id=author_data["author_id"],
                phone=author_data.get("phone"),
                city=author_data.get("city"),
                joined_date=_parse_date(author_data.get("joined_date")),
            )
            db.add(user)
            db.flush()

        authors_by_external[author_data["author_id"]] = user

        for book_data in author_data.get("books", []):
            existing_book = db.scalar(select(Book).where(Book.external_book_id == book_data["book_id"]))
            if existing_book:
                books_by_external[book_data["book_id"]] = existing_book
                continue

            book = Book(
                external_book_id=book_data["book_id"],
                author_id=user.id,
                title=book_data["title"],
                isbn=book_data.get("isbn"),
                genre=book_data.get("genre"),
                publication_date=_parse_date(book_data.get("publication_date")),
                status=book_data["status"],
                mrp=_optional_money(book_data.get("mrp")),
                author_royalty_per_copy=_optional_money(book_data.get("author_royalty_per_copy")),
                total_copies_sold=book_data.get("total_copies_sold") or 0,
                total_royalty_earned=_money(book_data.get("total_royalty_earned")),
                royalty_paid=_money(book_data.get("royalty_paid")),
                royalty_pending=_money(book_data.get("royalty_pending")),
                last_royalty_payout_date=_parse_date(book_data.get("last_royalty_payout_date")),
                print_partner=book_data.get("print_partner"),
            )
            db.add(book)
            db.flush()
            for platform in book_data.get("available_on") or []:
                db.add(BookPlatform(book_id=book.id, platform=platform))
            books_by_external[book_data["book_id"]] = book

    admin = db.scalar(select(User).where(User.email == settings.seed_admin_email.lower()))
    if not admin:
        admin = User(
            email=settings.seed_admin_email.lower(),
            password_hash=hash_password(settings.seed_admin_password),
            name=settings.seed_admin_name,
            role=UserRole.ADMIN,
        )
        db.add(admin)
        db.flush()

    _seed_sample_tickets(db, authors_by_external, books_by_external)
    db.commit()


def _seed_sample_tickets(
    db: Session,
    authors: dict[str, User],
    books: dict[str, Book],
) -> None:
    if db.scalar(select(Ticket.id).limit(1)):
        return

    samples = [
        {
            "number": "BL-2026-0001",
            "author": "AUTH003",
            "book": "BK005",
            "subject": "I published 4 months ago and still have not received any royalty",
            "description": (
                "Between Two Temples went live in July 2024. I can see royalty pending in the dashboard "
                "but there has never been a payout. Please tell me what is going on and when I will be paid."
            ),
            "category": TicketCategory.ROYALTY_PAYMENTS,
            "priority": TicketPriority.HIGH,
            "score": 80,
            "rationale": "Author has earned royalties with no payout date on record.",
        },
        {
            "number": "BL-2026-0002",
            "author": "AUTH001",
            "book": "BK001",
            "subject": "Royalty amount seems too low for the copies sold",
            "description": (
                "Whispers of the Ganges shows 342 copies sold and about ₹11,970 earned. "
                "That feels low against the MRP. Can I get a line-by-line breakdown?"
            ),
            "category": TicketCategory.ROYALTY_PAYMENTS,
            "priority": TicketPriority.MEDIUM,
            "score": 55,
            "rationale": "Payout exists; author is asking for a calculation explanation.",
        },
        {
            "number": "BL-2026-0003",
            "author": "AUTH007",
            "book": "BK013",
            "subject": "Midnight in Mysore has been stuck in cover design",
            "description": (
                "It has been weeks and Midnight in Mysore is still in Cover Design. "
                "When will typesetting start? I have not received a clear timeline."
            ),
            "category": TicketCategory.BOOK_STATUS,
            "priority": TicketPriority.MEDIUM,
            "score": 50,
            "rationale": "In-production title waiting on cover design; typical delay point.",
        },
        {
            "number": "BL-2026-0004",
            "author": "AUTH009",
            "book": "BK015",
            "subject": "Raising Roots still in typesetting after 3 weeks",
            "description": (
                "Raising Roots is still showing In Production - Typesetting. "
                "I need a realistic date for proofreading and ISBN assignment."
            ),
            "category": TicketCategory.BOOK_STATUS,
            "priority": TicketPriority.MEDIUM,
            "score": 50,
            "rationale": "Production delay at typesetting; needs an honest timeline.",
        },
    ]

    for item in samples:
        author = authors[item["author"]]
        book = books[item["book"]]
        ticket = Ticket(
            ticket_number=item["number"],
            author_id=author.id,
            book_id=book.id,
            subject=item["subject"],
            description=item["description"],
            category=item["category"],
            category_source=LabelSource.RULE,
            priority=item["priority"],
            priority_source=LabelSource.RULE,
            priority_score=item["score"],
            status=TicketStatus.OPEN,
            ai_draft_status=AiDraftStatus.PENDING,
            ai_rationale=item["rationale"],
        )
        db.add(ticket)
        db.flush()
        db.add(
            TicketMessage(
                ticket_id=ticket.id,
                sender_id=author.id,
                body=item["description"],
            )
        )
        db.add(
            TicketEvent(
                ticket_id=ticket.id,
                actor_id=author.id,
                event_type=TicketEventType.CREATED,
                payload={"source": "seed"},
            )
        )


def main() -> None:
    db = SessionLocal()
    try:
        seed(db)
        authors = db.scalars(select(User).where(User.role == UserRole.AUTHOR)).all()
        books = db.scalars(select(Book)).all()
        tickets = db.scalars(select(Ticket)).all()
        print(f"Seed complete: {len(authors)} authors, {len(books)} books, {len(tickets)} tickets")
    finally:
        db.close()


if __name__ == "__main__":
    main()
