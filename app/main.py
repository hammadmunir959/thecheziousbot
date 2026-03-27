from fastapi import FastAPI, Depends, HTTPException, status
from sqlmodel import Session
from .database.db import get_db, init_db
from .models import User
from .api.v1.router import api_router
from .api.v1.security import get_api_key
from contextlib import asynccontextmanager
import time


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Initializing database...")
    init_db()
    yield
    print("Cleanup complete.")


app = FastAPI(
    title="Chezious Pizza Bot",
    description="API for handling pizza orders via bot",
    lifespan=lifespan
)


@app.middleware("http")
async def add_process_time_header(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.get("/")
def root():
    return {
        "message": "Chezious Pizza Bot is live",
        "docs": "/docs",
        "health": "/ping"
    }


@app.get("/ping")
def ping():
    return {"ping": "pong"}


app.include_router(
    api_router,
    prefix="/api/v1",
    dependencies=[Depends(get_api_key)],
    tags=["v1"]
)