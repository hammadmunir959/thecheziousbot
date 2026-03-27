from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session
from .database.db import get_db, init_db
from .models import User
from .api.v1.router import api_router
from .api.v1.security import get_api_key
from contextlib import asynccontextmanager
import time
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up CheziousBot API...")
    init_db()
    yield
    logger.info("Shutting down CheziousBot API...")


app = FastAPI(
    title="CheziousBot API",
    version="1.0.0",
    description="API for handling pizza orders via bot",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
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
        "message": "Welcome to the CheziousBot API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/ping")
def ping():
    return {"ping": "pong"}


app.include_router(
    api_router,
    prefix="/api/v1",
    dependencies=[Depends(get_api_key)],
    tags=["v1"]
)