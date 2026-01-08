from typing import List, Optional
from decimal import Decimal
from app.models import Order, OrderType, OrderStyle, OrderStatus
from app.schemas import OrderRequest
from app.storage import storage
from app.exceptions import OrderValidationError, InstrumentNotFoundError


class OrderService:
    def __init__(self):
        self.storage = storage
    
    def place_order(self, order_request: OrderRequest) -> Order:
        self._validate_order_request(order_request)
        
        order = Order.create(
            symbol=order_request.symbol,
            order_type=order_request.order_type,
            order_style=order_request.order_style,
            quantity=order_request.quantity,
            price=order_request.price
        )
        
        # Update status to PLACED after creation
        order.status = OrderStatus.PLACED
        
        self.storage.save_order(order)
        
        # Auto-execute market orders
        if order.order_style == OrderStyle.MARKET:
            self._execute_market_order(order)
        
        return order
    
    def _execute_market_order(self, order: Order):
        """Execute a market order immediately"""
        from app.services.trade_service import trade_service
        try:
            trade_service.execute_market_order(order)
        except Exception as e:
            # If execution fails, keep order in PLACED status
            pass
    
    def get_order_status(self, order_id: str) -> Optional[Order]:
        return self.storage.get_order(order_id)
    
    def get_all_orders(self) -> List[Order]:
        return self.storage.get_all_orders()
    
    def update_order_status(self, order_id: str, status: OrderStatus) -> bool:
        return self.storage.update_order_status(order_id, status)
    
    def _validate_order_request(self, order_request: OrderRequest):
        # Validate quantity is positive (already handled by Pydantic Field(gt=0))
        if order_request.quantity <= 0:
            raise OrderValidationError("Order quantity must be greater than zero")
        
        # Validate limit orders have price
        if order_request.order_style == OrderStyle.LIMIT and order_request.price is None:
            raise OrderValidationError("Price is required for limit orders")
        
        # Validate price is positive for limit orders
        if order_request.order_style == OrderStyle.LIMIT and order_request.price is not None:
            if order_request.price <= 0:
                raise OrderValidationError("Price must be greater than zero for limit orders")
        
        # Validate instrument exists
        instrument = self.storage.get_instrument(order_request.symbol)
        if not instrument:
            raise InstrumentNotFoundError(order_request.symbol)


order_service = OrderService()