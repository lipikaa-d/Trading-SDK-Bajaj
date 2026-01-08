from fastapi import APIRouter, HTTPException, status
from app.schemas import OrderRequest, OrderResponse
from app.services.order_service import order_service
from app.exceptions import TradingAPIException, OrderNotFoundError

router = APIRouter()

@router.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def place_order(order: OrderRequest):
    # Exceptions are now handled by the global exception handlers
    placed_order = order_service.place_order(order)
    return OrderResponse(
        id=placed_order.id,
        symbol=placed_order.symbol,
        order_type=placed_order.order_type,
        order_style=placed_order.order_style,
        quantity=placed_order.quantity,
        price=placed_order.price,
        status=placed_order.status,
        created_at=placed_order.created_at
    )

@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order_status(order_id: str):
    order = order_service.get_order_status(order_id)
    if not order:
        raise OrderNotFoundError(order_id)
    
    return OrderResponse(
        id=order.id,
        symbol=order.symbol,
        order_type=order.order_type,
        order_style=order.order_style,
        quantity=order.quantity,
        price=order.price,
        status=order.status,
        created_at=order.created_at
    )

