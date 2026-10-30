from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.routers import admin as admin_router
from app.routers import auth as auth_router
from app.routers import books as books_router
from app.routers import events as events_router
from app.routers import tickets as tickets_router

settings = get_settings()

app = FastAPI(
    title="BookLeaf Author Support API",
    version="0.1.0",
    description="Author Support & Communication Portal — REST API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_exception_handlers(app)
app.include_router(auth_router.router)
app.include_router(books_router.router)
app.include_router(tickets_router.router)
app.include_router(admin_router.router)
app.include_router(events_router.router)


@app.get("/health", tags=["system"])
def health() -> dict:
    return {"status": "ok", "service": "bookleaf-api"}
