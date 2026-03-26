from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session
from .database.db import get_db, init_db
from .models import User
from .api.v1.router import api_router
from .api.v1.security import get_api_key
from contextlib import asynccontextmanager


app = FastAPI(title="CheziousBot API")



@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

    pass

 
# / root endpoint
@app.get("/")
def root():
    return {"message": "Welcome to the CheziousBot API"}


app.include_router(api_router, prefix="/api/v1", dependencies=[Depends(get_api_key)])

