from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.schemas.books import BookOut
from app.services.tickets import book_to_out, get_book_for_user, list_books_for_user

router = APIRouter(prefix="/api/v1/books", tags=["books"])


@router.get("", response_model=list[BookOut])
def list_books(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[BookOut]:
    return [book_to_out(book) for book in list_books_for_user(db, user)]


@router.get("/{book_id}", response_model=BookOut)
def get_book(book_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> BookOut:
    return book_to_out(get_book_for_user(db, user, book_id))
