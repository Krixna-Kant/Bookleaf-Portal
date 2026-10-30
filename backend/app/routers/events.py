from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.core.deps import get_current_user
from app.db.models import User
from app.services.realtime import event_stream

router = APIRouter(prefix="/api/v1/events", tags=["events"])


@router.get("/stream")
async def stream(user: User = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(
        event_stream(user.id, user.role),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )
