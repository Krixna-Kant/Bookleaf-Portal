from fastapi.testclient import TestClient

from app.enums import UserRole
from app.main import app
from app.services.realtime import event_visible_to, hub, publish_ticket_event

client = TestClient(app)


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main() -> None:
    expect(event_visible_to({"author_id": 1}, 1, UserRole.AUTHOR), "author should see own event")
    expect(not event_visible_to({"author_id": 2}, 1, UserRole.AUTHOR), "author should not see others")
    expect(event_visible_to({"author_id": 2}, 9, UserRole.ADMIN), "admin sees all")

    missing = client.get("/api/v1/events/stream")
    expect(missing.status_code == 401, missing.text)

    routes = {route.path for route in app.routes}
    expect("/api/v1/events/stream" in routes, routes)

    before = len(hub._subscribers)
    publish_ticket_event("ticket.created", 1, 1)
    expect(len(hub._subscribers) == before, "publish should not leak subscribers")
    print("REALTIME TESTS PASSED")


if __name__ == "__main__":
    main()
