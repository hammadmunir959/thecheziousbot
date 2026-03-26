from fastapi import APIRouter
from .endpoints import chat, users, orders

api_router = APIRouter()
api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
