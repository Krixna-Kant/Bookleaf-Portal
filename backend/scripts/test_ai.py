from fastapi.testclient import TestClient
from sqlalchemy import select

from app.ai.kb import category_slice, draft_context, estimate_tokens, tone_guide
from app.ai.rules import classify_ticket
from app.db.models import Book
from app.db.session import SessionLocal
from app.enums import TicketCategory, TicketPriority
from app.main import app

client = TestClient(app)


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main() -> None:
    category, priority, score, _why = classify_ticket(
        "I have not received any royalty",
        "It has been 6 months and no payout hit my bank.",
    )
    expect(category == TicketCategory.ROYALTY_PAYMENTS, category)
    expect(priority in {TicketPriority.CRITICAL, TicketPriority.HIGH}, priority)
    expect(score >= 75, score)

    isbn_cat, isbn_pri, *_ = classify_ticket("Wrong ISBN on Amazon", "The listing ISBN does not match the physical copy.")
    expect(isbn_cat == TicketCategory.ISBN_METADATA, isbn_cat)
    expect(isbn_pri == TicketPriority.HIGH, isbn_pri)

    tone = tone_guide()
    expect("partners" in tone.lower(), "tone missing partner language")
    slice_text = category_slice(TicketCategory.ROYALTY_PAYMENTS)
    expect("80/20" in slice_text, slice_text)
    context, tokens = draft_context(TicketCategory.ROYALTY_PAYMENTS)
    expect("ISBN" not in context or "ISBN Policy" not in context, "draft context should be category-sliced")
    expect(tokens < 800, f"slice too large: {tokens}")
    expect(estimate_tokens(tone) < estimate_tokens(tone, slice_text, "x" * 4000), "token helper")

    db = SessionLocal()
    book = db.scalar(select(Book).where(Book.external_book_id == "BK001"))
    db.close()
    token = client.post(
        "/api/v1/auth/login",
        json={"email": "priya.sharma@email.com", "password": "Author@123"},
    ).json()["access_token"]
    created = client.post(
        "/api/v1/tickets",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "book_id": book.id,
            "subject": "Can I update my author bio?",
            "description": "I want to change the short bio shown on Amazon after publication.",
        },
    )
    expect(created.status_code == 201, created.text)
    body = created.json()
    expect(body["category"] == "general", body["category"])
    expect(body["ai_draft_status"] in {"pending", "failed"}, body["ai_draft_status"])
    expect(body["status"] == "open", body)

    admin = client.post("/api/v1/auth/login", json={"email": "ops@bookleaf.com", "password": "Admin@123"}).json()
    regen = client.post(
        f"/api/v1/admin/tickets/{body['id']}/ai/regenerate-draft",
        headers={"Authorization": f"Bearer {admin['access_token']}"},
    )
    expect(regen.status_code == 200, regen.text)
    print("AI TESTS PASSED")


if __name__ == "__main__":
    main()
