import structlog
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles

from .config.settings import settings
from .core.logging import setup_logging, get_logger
from .middleware.error_handler import global_exception_handler, AppException
from .database.session import engine, Base
from .api.router import api_router
from .api.health import health_router

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AI-IDS application", version=settings.APP_VERSION, environment=settings.ENVIRONMENT)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")
    yield
    await engine.dispose()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise-Grade AI-Driven Intrusion Detection System",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("Request", method=request.method, path=request.url.path)
    response = await call_next(request)
    logger.info("Response", status=response.status_code)
    return response


app.add_exception_handler(Exception, global_exception_handler)


app.include_router(health_router, prefix="/api", tags=["Health"])
app.include_router(api_router, prefix="/api/v1", tags=["API"])


frontend_dist = (Path(__file__).parent / settings.FRONTEND_DIST_PATH).resolve()
frontend_index = frontend_dist / "index.html"
if frontend_dist.is_dir() and frontend_index.is_file():
    from fastapi.responses import FileResponse, HTMLResponse

    if (frontend_dist / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("openapi"):
            from fastapi.exceptions import HTTPException
            raise HTTPException(status_code=404)
        return HTMLResponse(frontend_index.read_bytes())

    logger.info("Frontend SPA mounted", path=str(frontend_dist))
else:
    logger.warning("Frontend dist not found, API-only mode", path=str(frontend_dist))

    @app.get("/")
    async def root():
        return {
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "running",
            "docs": "/api/docs",
        }


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Enterprise-Grade AI-Driven Intrusion Detection System",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {"url": "https://ai-ids.app/logo.png"}
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn
    import os

    port = int(os.getenv("PORT", str(settings.SERVER_PORT)))
    uvicorn.run(
        "main:app",
        host=settings.SERVER_HOST,
        port=port,
        reload=False,
        workers=settings.WORKERS,
        log_level=settings.LOG_LEVEL.lower(),
    )
