from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, computed_field

from app.enums import PAYOUT_THRESHOLD_INR


class BookOut(BaseModel):
    id: int
    external_book_id: str
    title: str
    isbn: str | None
    genre: str | None
    publication_date: date | None
    status: str
    mrp: Decimal | None
    author_royalty_per_copy: Decimal | None
    total_copies_sold: int
    total_royalty_earned: Decimal
    royalty_paid: Decimal
    royalty_pending: Decimal
    last_royalty_payout_date: date | None
    print_partner: str | None
    available_on: list[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}

    @computed_field
    @property
    def in_production(self) -> bool:
        return "production" in self.status.lower() or self.mrp is None

    @computed_field
    @property
    def below_payout_threshold(self) -> bool:
        return 0 < float(self.royalty_pending) < PAYOUT_THRESHOLD_INR
