from datetime import datetime, timezone

from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session, selectinload

from app.ai.rules import classify_ticket
from app.core.errors import AppError
from app.db.models import Book, Ticket, TicketEvent, TicketMessage, TicketNote, User
from app.enums import (
    PRIORITY_WEIGHT,
    AiDraftStatus,
    LabelSource,
    TicketCategory,
    TicketEventType,
    TicketPriority,
    TicketStatus,
    UserRole,
)
from app.schemas.auth import UserOut
from app.schemas.books import BookOut
from app.schemas.tickets import MessageOut, NoteOut, TicketDetail, TicketSummary
from app.services.realtime import publish_ticket_event


def next_ticket_number(db: Session) -> str:
    year = datetime.now(timezone.utc).year
    prefix = f"BL-{year}-"
    last = db.scalar(
        select(Ticket.ticket_number)
        .where(Ticket.ticket_number.like(f"{prefix}%"))
        .order_by(Ticket.ticket_number.desc())
        .limit(1)
    )
    sequence = 1
    if last:
        sequence = int(last.rsplit("-", 1)[-1]) + 1
    return f"{prefix}{sequence:04d}"


def _aging_hours(created_at: datetime) -> float:
    now = datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    return round((now - created_at).total_seconds() / 3600, 1)


def book_to_out(book: Book) -> BookOut:
    return BookOut(
        id=book.id,
        external_book_id=book.external_book_id,
        title=book.title,
        isbn=book.isbn,
        genre=book.genre,
        publication_date=book.publication_date,
        status=book.status,
        mrp=book.mrp,
        author_royalty_per_copy=book.author_royalty_per_copy,
        total_copies_sold=book.total_copies_sold,
        total_royalty_earned=book.total_royalty_earned,
        royalty_paid=book.royalty_paid,
        royalty_pending=book.royalty_pending,
        last_royalty_payout_date=book.last_royalty_payout_date,
        print_partner=book.print_partner,
        available_on=[platform.platform for platform in book.platforms],
    )


def _ticket_summary(ticket: Ticket) -> TicketSummary:
    return TicketSummary(
        id=ticket.id,
        ticket_number=ticket.ticket_number,
        subject=ticket.subject,
        status=ticket.status,
        category=ticket.category,
        category_source=ticket.category_source,
        priority=ticket.priority,
        priority_source=ticket.priority_source,
        priority_score=ticket.priority_score,
        book_id=ticket.book_id,
        book_title=ticket.book.title if ticket.book else None,
        author_id=ticket.author_id,
        author_name=ticket.author.name,
        assigned_to_id=ticket.assigned_to_id,
        assigned_to_name=ticket.assignee.name if ticket.assignee else None,
        ai_draft_status=ticket.ai_draft_status,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        aging_hours=_aging_hours(ticket.created_at),
    )


def ticket_to_detail(ticket: Ticket, *, include_notes: bool) -> TicketDetail:
    summary = _ticket_summary(ticket)
    return TicketDetail(
        **summary.model_dump(),
        description=ticket.description,
        ai_draft=ticket.ai_draft,
        ai_rationale=ticket.ai_rationale if include_notes else None,
        ai_confidence=ticket.ai_confidence,
        book=book_to_out(ticket.book) if ticket.book else None,
        author=UserOut.model_validate(ticket.author),
        messages=[
            MessageOut(
                id=message.id,
                sender_id=message.sender_id,
                sender_name=message.sender.name,
                sender_role=message.sender.role.value,
                body=message.body,
                created_at=message.created_at,
            )
            for message in ticket.messages
        ],
        notes=[
            NoteOut(
                id=note.id,
                admin_id=note.admin_id,
                admin_name=note.admin.name,
                body=note.body,
                created_at=note.created_at,
            )
            for note in ticket.notes
        ]
        if include_notes
        else [],
    )


def _ticket_load_options():
    return (
        selectinload(Ticket.book).selectinload(Book.platforms),
        selectinload(Ticket.author),
        selectinload(Ticket.assignee),
        selectinload(Ticket.messages).selectinload(TicketMessage.sender),
        selectinload(Ticket.notes).selectinload(TicketNote.admin),
    )


def get_ticket(db: Session, ticket_id: int) -> Ticket:
    ticket = db.scalar(select(Ticket).options(*_ticket_load_options()).where(Ticket.id == ticket_id))
    if ticket is None:
        raise AppError("TICKET_NOT_FOUND", "Ticket was not found", 404)
    return ticket


def create_ticket(db: Session, author: User, book_id: int | None, subject: str, description: str) -> Ticket:
    book = None
    if book_id is not None:
        book = db.scalar(select(Book).where(Book.id == book_id, Book.author_id == author.id))
        if book is None:
            raise AppError("BOOK_NOT_FOUND", "That book is not on your account", 404)

    category, priority, score, rationale = classify_ticket(subject, description)
    ticket = Ticket(
        ticket_number=next_ticket_number(db),
        author_id=author.id,
        book_id=book.id if book else None,
        subject=subject,
        description=description,
        category=category,
        category_source=LabelSource.RULE,
        priority=priority,
        priority_source=LabelSource.RULE,
        priority_score=score,
        status=TicketStatus.OPEN,
        ai_draft_status=AiDraftStatus.PENDING,
        ai_rationale=rationale,
    )
    db.add(ticket)
    db.flush()
    db.add(TicketMessage(ticket_id=ticket.id, sender_id=author.id, body=description))
    db.add(
        TicketEvent(
            ticket_id=ticket.id,
            actor_id=author.id,
            event_type=TicketEventType.CREATED,
            payload={"category": category.value, "priority": priority.value},
        )
    )
    db.commit()
    db.expire_all()
    loaded = get_ticket(db, ticket.id)
    publish_ticket_event("ticket.created", loaded.id, loaded.author_id)
    return loaded


def list_author_tickets(db: Session, author_id: int) -> list[Ticket]:
    return list(
        db.scalars(
            select(Ticket)
            .options(*_ticket_load_options())
            .where(Ticket.author_id == author_id)
            .order_by(Ticket.created_at.desc())
        ).unique()
    )


def apply_queue_filters(
    stmt: Select,
    *,
    status: TicketStatus | None,
    category: TicketCategory | None,
    priority: TicketPriority | None,
    q: str | None,
) -> Select:
    if status:
        stmt = stmt.where(Ticket.status == status)
    if category:
        stmt = stmt.where(Ticket.category == category)
    if priority:
        stmt = stmt.where(Ticket.priority == priority)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.join(Ticket.author).where(
            or_(Ticket.subject.ilike(like), Ticket.ticket_number.ilike(like), User.name.ilike(like))
        )
    return stmt


def list_admin_tickets(
    db: Session,
    *,
    status: TicketStatus | None = None,
    category: TicketCategory | None = None,
    priority: TicketPriority | None = None,
    q: str | None = None,
    sort: str = "urgency",
) -> list[Ticket]:
    stmt = select(Ticket).options(*_ticket_load_options())
    stmt = apply_queue_filters(stmt, status=status, category=category, priority=priority, q=q)
    if sort == "newest":
        stmt = stmt.order_by(Ticket.created_at.desc())
    else:
        stmt = stmt.order_by(Ticket.priority_score.desc(), Ticket.created_at.asc())
    return list(db.scalars(stmt).unique())


def patch_ticket(
    db: Session,
    ticket: Ticket,
    admin: User,
    *,
    status: TicketStatus | None,
    category: TicketCategory | None,
    priority: TicketPriority | None,
    assigned_to_id: int | None,
) -> Ticket:
    changes: dict = {}
    if status is not None and status != ticket.status:
        ticket.status = status
        changes["status"] = status.value
        if status in (TicketStatus.RESOLVED, TicketStatus.CLOSED):
            ticket.resolved_at = datetime.now(timezone.utc)
        else:
            ticket.resolved_at = None
    if category is not None and category != ticket.category:
        ticket.category = category
        ticket.category_source = LabelSource.ADMIN
        changes["category"] = category.value
    if priority is not None and priority != ticket.priority:
        ticket.priority = priority
        ticket.priority_source = LabelSource.ADMIN
        ticket.priority_score = PRIORITY_WEIGHT[priority]
        changes["priority"] = priority.value
    if assigned_to_id is not None:
        assignee = db.scalar(select(User).where(User.id == assigned_to_id, User.role == UserRole.ADMIN))
        if assignee is None:
            raise AppError("ASSIGNEE_NOT_FOUND", "Assignee must be an admin", 400)
        ticket.assigned_to_id = assignee.id
        changes["assigned_to_id"] = assignee.id
    if changes:
        db.add(
            TicketEvent(
                ticket_id=ticket.id,
                actor_id=admin.id,
                event_type=TicketEventType.UPDATED,
                payload=changes,
            )
        )
    db.commit()
    db.expire_all()
    loaded = get_ticket(db, ticket.id)
    publish_ticket_event("ticket.updated", loaded.id, loaded.author_id)
    return loaded


def assign_to_self(db: Session, ticket: Ticket, admin: User) -> Ticket:
    ticket.assigned_to_id = admin.id
    if ticket.status == TicketStatus.OPEN:
        ticket.status = TicketStatus.IN_PROGRESS
    db.add(
        TicketEvent(
            ticket_id=ticket.id,
            actor_id=admin.id,
            event_type=TicketEventType.ASSIGNED,
            payload={"assigned_to_id": admin.id},
        )
    )
    db.commit()
    db.expire_all()
    loaded = get_ticket(db, ticket.id)
    publish_ticket_event("ticket.updated", loaded.id, loaded.author_id)
    return loaded


def add_note(db: Session, ticket: Ticket, admin: User, body: str) -> Ticket:
    db.add(TicketNote(ticket_id=ticket.id, admin_id=admin.id, body=body))
    db.add(
        TicketEvent(
            ticket_id=ticket.id,
            actor_id=admin.id,
            event_type=TicketEventType.NOTE_ADDED,
            payload={},
        )
    )
    db.commit()
    db.expire_all()
    loaded = get_ticket(db, ticket.id)
    publish_ticket_event("ticket.updated", loaded.id, loaded.author_id)
    return loaded


def add_reply(db: Session, ticket: Ticket, admin: User, body: str) -> Ticket:
    db.add(TicketMessage(ticket_id=ticket.id, sender_id=admin.id, body=body))
    if ticket.status == TicketStatus.OPEN:
        ticket.status = TicketStatus.IN_PROGRESS
    if ticket.assigned_to_id is None:
        ticket.assigned_to_id = admin.id
    if ticket.ai_draft and ticket.ai_draft_status == AiDraftStatus.READY:
        ticket.ai_draft_status = AiDraftStatus.SENT
    db.add(
        TicketEvent(
            ticket_id=ticket.id,
            actor_id=admin.id,
            event_type=TicketEventType.REPLIED,
            payload={},
        )
    )
    db.commit()
    db.expire_all()
    loaded = get_ticket(db, ticket.id)
    publish_ticket_event("ticket.message", loaded.id, loaded.author_id)
    return loaded


def admin_stats(db: Session) -> dict:
    now = datetime.now(timezone.utc)
    rows = db.execute(select(Ticket.status, Ticket.priority, Ticket.created_at)).all()
    stats = {
        "open": 0,
        "in_progress": 0,
        "resolved": 0,
        "closed": 0,
        "critical": 0,
        "high": 0,
        "aging_over_48h": 0,
    }
    for status, priority, created_at in rows:
        stats[status.value] += 1
        if priority == TicketPriority.CRITICAL:
            stats["critical"] += 1
        if priority == TicketPriority.HIGH:
            stats["high"] += 1
        created = created_at if created_at.tzinfo else created_at.replace(tzinfo=timezone.utc)
        if status in (TicketStatus.OPEN, TicketStatus.IN_PROGRESS) and (now - created).total_seconds() > 48 * 3600:
            stats["aging_over_48h"] += 1
    return stats


def list_books_for_user(db: Session, user: User) -> list[Book]:
    stmt = select(Book).options(selectinload(Book.platforms)).order_by(Book.title)
    if user.role == UserRole.AUTHOR:
        stmt = stmt.where(Book.author_id == user.id)
    return list(db.scalars(stmt).unique())


def get_book_for_user(db: Session, user: User, book_id: int) -> Book:
    stmt = select(Book).options(selectinload(Book.platforms)).where(Book.id == book_id)
    if user.role == UserRole.AUTHOR:
        stmt = stmt.where(Book.author_id == user.id)
    book = db.scalar(stmt)
    if book is None:
        raise AppError("BOOK_NOT_FOUND", "Book was not found", 404)
    return book
