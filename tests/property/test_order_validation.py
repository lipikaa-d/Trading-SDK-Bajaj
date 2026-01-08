import pytest
from hypothesis import given, strategies as st, assume
from decimal import Decimal
from app.services.order_service import OrderService, OrderValidationError
from app.schemas import OrderRequest
from app.models import OrderType, OrderStyle


class TestOrderValidationProperties:
    
    def setup_method(self):
        self.order_service = OrderService()
    
    @given(
        quantity=st.integers(min_value=1, max_value=10000),
        order_type=st.sampled_from(OrderType),
    )
    def test_order_validation_rules_market_orders(self, quantity, order_type):
        """
        Feature: trading-api-sdk, Property 2: Order Validation Rules
        For any order placement request, market orders with positive quantity should be accepted
        """
        order_request = OrderRequest(
            symbol="TCS",  # Valid symbol from sample data
            order_type=order_type,
            order_style=OrderStyle.MARKET,
            quantity=quantity,
            price=None
        )
        
        # Market orders with positive quantity should be accepted
        order = self.order_service.place_order(order_request)
        assert order is not None
        assert order.quantity == quantity
        assert order.order_type == order_type
        assert order.order_style == OrderStyle.MARKET
    
    @given(
        quantity=st.integers(min_value=1, max_value=10000),
        price=st.decimals(min_value=Decimal('0.01'), max_value=Decimal('10000'), places=2),
        order_type=st.sampled_from(OrderType),
    )
    def test_order_validation_rules_limit_orders(self, quantity, price, order_type):
        """
        Feature: trading-api-sdk, Property 2: Order Validation Rules
        For any order placement request, limit orders should require both positive quantity and price
        """
        order_request = OrderRequest(
            symbol="TCS",
            order_type=order_type,
            order_style=OrderStyle.LIMIT,
            quantity=quantity,
            price=price
        )
        
        # Limit orders with positive quantity and price should be accepted
        order = self.order_service.place_order(order_request)
        assert order is not None
        assert order.quantity == quantity
        assert order.price == price
        assert order.order_style == OrderStyle.LIMIT
    
    @given(
        quantity=st.integers(max_value=0),  # Zero or negative
        order_type=st.sampled_from(OrderType),
        order_style=st.sampled_from(OrderStyle),
    )
    def test_invalid_order_rejection_quantity(self, quantity, order_type, order_style):
        """
        Feature: trading-api-sdk, Property 3: Invalid Order Rejection
        For any order with zero or negative quantity, the system should reject it with an appropriate error
        """
        price = Decimal('100.00') if order_style == OrderStyle.LIMIT else None
        
        # Pydantic validation should catch invalid quantities at schema level
        with pytest.raises((OrderValidationError, ValueError, Exception)):  # Include pydantic validation errors
            order_request = OrderRequest(
                symbol="TCS",
                order_type=order_type,
                order_style=order_style,
                quantity=quantity,
                price=price
            )
            # If schema validation passes (shouldn't happen), service validation should catch it
            self.order_service.place_order(order_request)
    
    @given(
        quantity=st.integers(min_value=1, max_value=10000),
        order_type=st.sampled_from(OrderType),
    )
    def test_invalid_order_rejection_limit_without_price(self, quantity, order_type):
        """
        Feature: trading-api-sdk, Property 3: Invalid Order Rejection
        For any limit order without price, the system should reject it with an appropriate error
        """
        order_request = OrderRequest(
            symbol="TCS",
            order_type=order_type,
            order_style=OrderStyle.LIMIT,
            quantity=quantity,
            price=None
        )
        
        with pytest.raises(OrderValidationError):
            self.order_service.place_order(order_request)
    
    @given(
        quantity=st.integers(min_value=1, max_value=10000),
        price=st.one_of(st.none(), st.decimals(min_value=Decimal('0.01'), max_value=Decimal('10000'), places=2)),
        order_type=st.sampled_from(OrderType),
        order_style=st.sampled_from(OrderStyle),
    )
    def test_order_type_and_style_support(self, quantity, price, order_type, order_style):
        """
        Feature: trading-api-sdk, Property 4: Order Type and Style Support
        For any valid order request, the system should accept both BUY/SELL types and MARKET/LIMIT styles
        """
        # Ensure limit orders have price
        if order_style == OrderStyle.LIMIT and price is None:
            price = Decimal('100.00')
        elif order_style == OrderStyle.MARKET:
            price = None
        
        order_request = OrderRequest(
            symbol="TCS",
            order_type=order_type,
            order_style=order_style,
            quantity=quantity,
            price=price
        )
        
        order = self.order_service.place_order(order_request)
        assert order.order_type == order_type
        assert order.order_style == order_style
    
    def test_unique_order_identifiers(self):
        """
        Feature: trading-api-sdk, Property 5: Unique Order Identifiers
        For any sequence of successfully placed orders, all order IDs should be unique
        """
        order_ids = set()
        
        for i in range(100):
            order_request = OrderRequest(
                symbol="TCS",
                order_type=OrderType.BUY,
                order_style=OrderStyle.MARKET,
                quantity=10,
                price=None
            )
            
            order = self.order_service.place_order(order_request)
            assert order.id not in order_ids, f"Duplicate order ID found: {order.id}"
            order_ids.add(order.id)