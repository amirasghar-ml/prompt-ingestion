from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import engine, Base
from app.routers import prompts, ingest

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Prompt Ingestion API",
    description=(
        "A service for ingesting, storing, versioning, and serving prompts "
        "from multiple sources (API, file upload, bulk JSON/CSV)."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers
app.include_router(prompts.router, prefix="/api")
app.include_router(ingest.router, prefix="/api")

# Serve the web UI
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", include_in_schema=False)
def serve_ui():
    return FileResponse("static/index.html")


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
