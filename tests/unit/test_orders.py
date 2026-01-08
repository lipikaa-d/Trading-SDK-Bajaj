import pytest
from decimal import Decimal
from app.services.order_service import OrderService, OrderValidationError
from app.schemas import OrderRequest
from app.models import OrderType, OrderStyle, OrderStatus


class TestOrderService:
    
    def setup_method(self):
        self.order_service = OrderService()
    
    def test_place_market_order_success(self):
        order_request = OrderRequest(
            symbol="TCS",
            order_type=OrderType.BUY,
            order_style=OrderStyle.MARKET,
            quantity=100,
            price=None
        )
        
        order = self.order_service.place_order(order_request)
        
        assert order is not None
        assert order.symbol == "TCS"
        assert order.order_type == OrderType.BUY
        assert order.order_style == OrderStyle.MARKET
        assert order.quantity == 100
        assert order.price is None
        assert order.status == OrderStatus.PLACED
        assert order.id is not None
    
    def test_place_limit_order_success(self):
        order_request = OrderRequest(
            symbol="INFY",
            order_type=OrderType.SELL,
            order_style=OrderStyle.LIMIT,
            quantity=50,
            price=Decimal("1500.00")
        )
        
        order = self.order_service.place_order(order_request)
        
        assert order is not None
        assert order.symbol == "INFY"
        assert order.order_type == OrderType.SELL
        assert order.order_style == OrderStyle.LIMIT
        assert order.quantity == 50
        assert order.price == Decimal("1500.00")
        assert order.status == OrderStatus.PLACED
    
    def test_place_order_invalid_symbol(self):
        order_request = OrderRequest(
            symbol="INVALID",
            order_type=OrderType.BUY,
            order_style=OrderStyle.MARKET,
            quantity=100,
            price=None
        )
        
        with pytest.raises(OrderValidationError, match="Instrument INVALID not found"):
            self.order_service.place_order(order_request)
    
    def test_place_limit_order_without_price(self):
        order_request = OrderRequest(
            symbol="TCS",
            order_type=OrderType.BUY,
            order_style=OrderStyle.LIMIT,
            quantity=100,
            price=None
        )
        
        with pytest.raises(OrderValidationError, match="Price is required for limit orders"):
            self.order_service.place_order(order_request)
    
    def test_place_limit_order_negative_price(self):
        order_request = OrderRequest(
            symbol="TCS",
            order_type=OrderType.BUY,
            order_style=OrderStyle.LIMIT,
            quantity=100,
            price=Decimal("-10.00")
        )
        
        with pytest.raises(OrderValidationError, match="Price must be greater than zero"):
            self.order_service.place_order(order_request)
    
    def test_get_order_status_existing(self):
        order_request = OrderRequest(
            symbol="TCS",
            order_type=OrderType.BUY,
            order_style=OrderStyle.MARKET,
            quantity=100,
            price=None
        )
        
        placed_order = self.order_service.place_order(order_request)
        retrieved_order = self.order_service.get_order_status(placed_order.id)
        
        assert retrieved_order is not None
        assert retrieved_order.id == placed_order.id
        assert retrieved_order.status == OrderStatus.PLACED
    
    def test_get_order_status_nonexistent(self):
        result = self.order_service.get_order_status("nonexistent-id")
        assert result is None
    
    def test_update_order_status_success(self):
        order_request = OrderRequest(
            symbol="TCS",
            order_type=OrderType.BUY,
            order_style=OrderStyle.MARKET,
            quantity=100,
            price=None
        )
        
        order = self.order_service.place_order(order_request)
        success = self.order_service.update_order_status(order.id, OrderStatus.EXECUTED)
        
        assert success is True
        
        updated_order = self.order_service.get_order_status(order.id)
        assert updated_order.status == OrderStatus.EXECUTED
    
    def test_update_order_status_nonexistent(self):
        success = self.order_service.update_order_status("nonexistent-id", OrderStatus.EXECUTED)
        assert success is False
    
    def test_order_state_transitions(self):
        order_request = OrderRequest(
            symbol="TCS",
            order_type=OrderType.BUY,
            order_style=OrderStyle.MARKET,
            quantity=100,
            price=None
        )
        
        # NEW -> PLACED (happens in place_order)
        order = self.order_service.place_order(order_request)
        assert order.status == OrderStatus.PLACED
        
        # PLACED -> EXECUTED
        self.order_service.update_order_status(order.id, OrderStatus.EXECUTED)
        updated_order = self.order_service.get_order_status(order.id)
        assert updated_order.status == OrderStatus.EXECUTED
        
        # EXECUTED -> CANCELLED (edge case, but should work)
        self.order_service.update_order_status(order.id, OrderStatus.CANCELLED)
        final_order = self.order_service.get_order_status(order.id)
        assert final_order.status == OrderStatus.CANCELLED