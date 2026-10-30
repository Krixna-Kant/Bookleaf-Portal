from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_author
from app.core.errors import AppError
from app.db.models import User
from app.db.session import get_db
from app.schemas.tickets import TicketCreate, TicketDetail, TicketSummary
from app.services.tickets import create_ticket, get_ticket, list_author_tickets, ticket_to_detail, _ticket_summary

router = APIRouter(prefix="/api/v1/tickets", tags=["tickets"])


@router.post("", response_model=TicketDetail, status_code=201)
def create_author_ticket(
    body: TicketCreate,
    user: User = Depends(require_author),
    db: Session = Depends(get_db),
) -> TicketDetail:
    ticket = create_ticket(db, user, body.book_id, body.subject, body.description)
    return ticket_to_detail(ticket, include_notes=False)


@router.get("", response_model=list[TicketSummary])
def list_my_tickets(user: User = Depends(require_author), db: Session = Depends(get_db)) -> list[TicketSummary]:
    return [_ticket_summary(ticket) for ticket in list_author_tickets(db, user.id)]


@router.get("/{ticket_id}", response_model=TicketDetail)
def get_my_ticket(
    ticket_id: int,
    user: User = Depends(require_author),
    db: Session = Depends(get_db),
) -> TicketDetail:
    ticket = get_ticket(db, ticket_id)
    if ticket.author_id != user.id:
        raise AppError("TICKET_NOT_FOUND", "Ticket was not found", 404)
    return ticket_to_detail(ticket, include_notes=False)
