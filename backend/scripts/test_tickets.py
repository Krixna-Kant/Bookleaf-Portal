from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import Book, Ticket
from app.db.session import SessionLocal
from app.main import app

client = TestClient(app)


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def login(email: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    expect(response.status_code == 200, f"login {email} {response.text}")
    return response.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def main() -> None:
    db = SessionLocal()
    rohit_book = db.scalar(select(Book).where(Book.external_book_id == "BK003"))
    priya_book = db.scalar(select(Book).where(Book.external_book_id == "BK001"))
    ananya_ticket = db.scalar(select(Ticket).where(Ticket.ticket_number == "BL-2026-0001"))
    db.close()

    priya_token = login("priya.sharma@email.com", "Author@123")
    sneha_token = login("sneha.kulkarni@email.com", "Author@123")
    admin_token = login("ops@bookleaf.com", "Admin@123")

    books = client.get("/api/v1/books", headers=auth(priya_token))
    expect(books.status_code == 200, books.text)
    ids = {item["external_book_id"] for item in books.json()}
    expect(ids == {"BK001", "BK002"}, ids)
    expect(any(item["below_payout_threshold"] is False for item in books.json()), books.json())

    sneha_books = client.get("/api/v1/books", headers=auth(sneha_token)).json()
    prod = next(item for item in sneha_books if item["external_book_id"] == "BK013")
    expect(prod["in_production"] is True, prod)
    expect(prod["mrp"] is None, prod)

    forbidden_book = client.get(f"/api/v1/books/{rohit_book.id}", headers=auth(priya_token))
    expect(forbidden_book.status_code == 404, forbidden_book.text)

    own_book = client.get(f"/api/v1/books/{priya_book.id}", headers=auth(priya_token))
    expect(own_book.status_code == 200, own_book.text)

    leaked = client.get(f"/api/v1/tickets/{ananya_ticket.id}", headers=auth(priya_token))
    expect(leaked.status_code == 404, leaked.text)

    created = client.post(
        "/api/v1/tickets",
        headers=auth(priya_token),
        json={
            "book_id": priya_book.id,
            "subject": "I have not received royalty for months",
            "description": "Whispers of the Ganges still has pending royalty and I have not received a payout explanation.",
        },
    )
    expect(created.status_code == 201, f"create status {created.status_code} {created.text}")
    created_body = created.json()
    expect(created_body["category"] == "royalty_payments", f"category {created_body['category']}")
    expect(created_body["priority"] in {"critical", "high"}, f"priority {created_body['priority']}")
    expect(created_body["notes"] == [], f"notes leaked {created_body['notes']}")

    other_book = client.post(
        "/api/v1/tickets",
        headers=auth(priya_token),
        json={"book_id": rohit_book.id, "subject": "Wrong book selected here", "description": "This should be rejected because the book is not mine."},
    )
    expect(other_book.status_code == 404, other_book.text)

    admin_forbidden = client.get("/api/v1/admin/tickets", headers=auth(priya_token))
    expect(admin_forbidden.status_code == 403, admin_forbidden.text)

    queue = client.get("/api/v1/admin/tickets", headers=auth(admin_token))
    expect(queue.status_code == 200, f"queue {queue.status_code} {queue.text}")
    expect(len(queue.json()) >= 5, f"queue size {len(queue.json())}")
    expect(
        queue.json()[0]["priority_score"] >= queue.json()[-1]["priority_score"],
        "queue is not urgency-sorted",
    )

    stats = client.get("/api/v1/admin/stats", headers=auth(admin_token))
    expect(stats.status_code == 200, stats.text)
    expect(stats.json()["open"] >= 5, stats.json())

    note = client.post(
        f"/api/v1/admin/tickets/{created_body['id']}/notes",
        headers=auth(admin_token),
        json={"body": "Check bank details before promising a date."},
    )
    expect(note.status_code == 200, note.text)
    expect(len(note.json()["notes"]) == 1, note.json())

    override = client.patch(
        f"/api/v1/admin/tickets/{created_body['id']}",
        headers=auth(admin_token),
        json={"priority": "high"},
    )
    expect(override.json()["priority"] == "high", override.json())
    expect(override.json()["priority_source"] == "admin", override.json())

    reply = client.post(
        f"/api/v1/admin/tickets/{created_body['id']}/replies",
        headers=auth(admin_token),
        json={"body": "We are checking your payout window and will update you within 48 hours."},
    )
    expect(reply.status_code == 200, reply.text)
    expect(reply.json()["status"] == "in_progress", reply.json())
    expect(len(reply.json()["messages"]) == 2, reply.json())

    author_view = client.get(f"/api/v1/tickets/{created_body['id']}", headers=auth(priya_token))
    expect(author_view.status_code == 200, author_view.text)
    expect(len(author_view.json()["messages"]) == 2, author_view.json())
    expect(author_view.json()["notes"] == [], author_view.json())
    expect("Check bank details" not in author_view.text, author_view.text)

    print("TICKET TESTS PASSED")


if __name__ == "__main__":
    main()
