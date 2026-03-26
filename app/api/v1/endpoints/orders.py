from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List, Optional, Union
from ....database.db import get_db
from ....services.services import get_order, get_user_orders, OrderNotFoundError, ServiceError
from ....schemas.schemas import OrderResponse, OrderItemResponse, OrderListResponse

router = APIRouter()

@router.get("/{user_id}", response_model=Union[OrderResponse, OrderListResponse])
def get_user_order_details(
    user_id: str, 
    order_id: Optional[str] = Query(None), 
    db: Session = Depends(get_db)
):
    """
    Get details for a specific order or list all orders belonging to a user.
    """
    
    try:
        if order_id:
            # Single Order
            o = get_order(order_id, user_id=user_id)
            
            item_list = []
            for item in o.items:
                item_list.append(OrderItemResponse(
                    item_name=item.item_name,
                    qty=item.qty,
                    price=item.price,
                    total=item.total
                ))
                
            return OrderResponse(
                id=o.id,
                user_id=o.user_id,
                status=o.status,
                payment_method=o.payment_method,
                created_at=o.created_at,
                delivery_address=o.delivery_address,
                total_bill=o.total_bill,
                items=item_list
             )
        else:
            # List all orders
            orders = get_user_orders(user_id)
            order_list = []
            for o in orders:
                item_list = []
                for item in o.items:
                    item_list.append(OrderItemResponse(
                        item_name=item.item_name,
                        qty=item.qty,
                        price=item.price,
                        total=item.total
                    ))
                
                order_list.append(OrderResponse(
                    id=o.id,
                    user_id=o.user_id,
                    status=o.status,
                    payment_method=o.payment_method,
                    created_at=o.created_at,
                    delivery_address=o.delivery_address,
                    total_bill=o.total_bill,
                    items=item_list
                ))
            return OrderListResponse(orders=order_list)
            
    except OrderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
