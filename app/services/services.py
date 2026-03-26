"""
services.py — Centralized business logic for CheziousBot.
"""
import logging
from typing import List, Optional
from sqlmodel import select, Session
from sqlalchemy.orm import selectinload
from ..database.db import engine
from ..models.order_model import Order as OrderModel, OrderItem
from ..models.users_model import User as UserModel
from ..schemas.schemas import MenuItem


class ServiceError(Exception): pass
class UserNotFoundError(ServiceError): pass
class OrderNotFoundError(ServiceError): pass

def get_order(order_id: str, user_id: Optional[str] = None) -> OrderModel:
    """Retrieve order with eager-loaded relations, optionally filtered by user."""
    with Session(engine) as session:
        stmt = select(OrderModel).where(OrderModel.id == order_id)
        if user_id:
            stmt = stmt.where(OrderModel.user_id == user_id)
        
        order = session.exec(stmt.options(selectinload(OrderModel.user), selectinload(OrderModel.items))).first()
        if not order:
            raise OrderNotFoundError(f"Order '{order_id}' not found.")
        return order

def get_user_orders(user_id: str) -> List[OrderModel]:
    """Retrieve all orders for a user."""
    with Session(engine) as session:
        orders = session.exec(
            select(OrderModel).where(OrderModel.user_id == user_id)
            .options(selectinload(OrderModel.items)).order_by(OrderModel.created_at.desc())
        ).all()
        return list(orders)


def create_order(user_id: str, items: List[MenuItem], delivery_address: str, payment_method: str) -> OrderModel:
    """Create a new order for a user."""
    with Session(engine) as session:
        user = session.get(UserModel, user_id)
        if not user:
            raise UserNotFoundError(f"User '{user_id}' not found.")

        order = OrderModel(
            user_id=user.id,
            status="created",
            payment_method=payment_method.lower(),
            delivery_address=delivery_address.strip(),
        )
        
        for itm in items:
            order.items.append(OrderItem(item_name=itm.item, qty=itm.quantity, price=itm.price))

        session.add(order)
        session.flush()
        order.compute_total()
        session.commit()
        return get_order(order.id, user_id=user.id)

