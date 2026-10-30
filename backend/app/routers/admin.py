from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from app.ai.pipeline import run_ai_pipeline
from app.core.deps import require_admin
from app.enums import AiDraftStatus
from app.db.models import User
from app.db.session import get_db
from app.enums import TicketCategory, TicketPriority, TicketStatus
from app.schemas.tickets import AdminStats, MessageCreate, NoteCreate, TicketDetail, TicketPatch, TicketSummary
from app.services.tickets import (
    _ticket_summary,
    add_note,
    add_reply,
    admin_stats,
    assign_to_self,
    get_ticket,
    list_admin_tickets,
    patch_ticket,
    ticket_to_detail,
)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/stats", response_model=AdminStats)
def get_stats(user: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    return admin_stats(db)


@router.get("/tickets", response_model=list[TicketSummary])
def queue(
    status: TicketStatus | None = None,
    category: TicketCategory | None = None,
    priority: TicketPriority | None = None,
    q: str | None = Query(default=None, max_length=120),
    sort: str = Query(default="urgency"),
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[TicketSummary]:
    tickets = list_admin_tickets(db, status=status, category=category, priority=priority, q=q, sort=sort)
    return [_ticket_summary(ticket) for ticket in tickets]


@router.get("/tickets/{ticket_id}", response_model=TicketDetail)
def get_admin_ticket(
    ticket_id: int,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> TicketDetail:
    return ticket_to_detail(get_ticket(db, ticket_id), include_notes=True)


@router.patch("/tickets/{ticket_id}", response_model=TicketDetail)
def update_ticket(
    ticket_id: int,
    body: TicketPatch,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> TicketDetail:
    ticket = get_ticket(db, ticket_id)
    updated = patch_ticket(
        db,
        ticket,
        user,
        status=body.status,
        category=body.category,
        priority=body.priority,
        assigned_to_id=body.assigned_to_id,
    )
    return ticket_to_detail(updated, include_notes=True)


@router.post("/tickets/{ticket_id}/assign", response_model=TicketDetail)
def assign_ticket(
    ticket_id: int,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> TicketDetail:
    return ticket_to_detail(assign_to_self(db, get_ticket(db, ticket_id), user), include_notes=True)


@router.post("/tickets/{ticket_id}/notes", response_model=TicketDetail)
def create_note(
    ticket_id: int,
    body: NoteCreate,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> TicketDetail:
    return ticket_to_detail(add_note(db, get_ticket(db, ticket_id), user, body.body), include_notes=True)


@router.post("/tickets/{ticket_id}/ai/regenerate-draft", response_model=TicketDetail)
def regenerate_draft(
    ticket_id: int,
    background: BackgroundTasks,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> TicketDetail:
    ticket = get_ticket(db, ticket_id)
    ticket.ai_draft_status = AiDraftStatus.PENDING
    db.commit()
    background.add_task(run_ai_pipeline, ticket.id)
    return ticket_to_detail(get_ticket(db, ticket.id), include_notes=True)


@router.post("/tickets/{ticket_id}/replies", response_model=TicketDetail)
def create_reply(
    ticket_id: int,
    body: MessageCreate,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> TicketDetail:
    return ticket_to_detail(add_reply(db, get_ticket(db, ticket_id), user, body.body), include_notes=True)
