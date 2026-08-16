from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, physical_evaluation, training, examinations, org, fpet
from app.startup import run_startup_tasks

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(physical_evaluation.router)
app.include_router(training.router)
app.include_router(examinations.router)
 app.include_router(fpet.router)


@app.on_event("startup")
async def on_startup():
    # Safe to run on every boot -- both steps check for existing data
    # first and skip if already present. This is what lets a free-tier
    # deployment (no Shell access) initialize itself automatically.
    await run_startup_tasks()


@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok"}
