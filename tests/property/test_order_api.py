import pytest
from hypothesis import given, strategies as st
from fastapi.testclient import TestClient
from decimal import Decimal
from app.main import app
from app.models import OrderType, OrderStyle


client = TestClient(app)


class TestOrderAPIProperties:
    
    @given(
        quantity=st.integers(min_value=1, max_value=1000),
        order_type=st.sampled_from(OrderType),
    )
    def test_order_status_retrieval(self, quantity, order_type):
        """
        Feature: trading-api-sdk, Property 6: Order Status Retrieval
        For any valid order ID, querying the order should return the current status
        """
        # Place an order first
        order_data = {
            "symbol": "TCS",
            "order_type": order_type.value,
            "order_style": "MARKET",
            "quantity": quantity,
            "price": None
        }
        
        place_response = client.post("/api/v1/orders", json=order_data)
        assert place_response.status_code == 200
        
        placed_order = place_response.json()
        order_id = placed_order["id"]
        
        # Query the order status
        status_response = client.get(f"/api/v1/orders/{order_id}")
        assert status_response.status_code == 200
        
        retrieved_order = status_response.json()
        assert retrieved_order["id"] == order_id
        assert retrieved_order["status"] in ["NEW", "PLACED", "EXECUTED", "CANCELLED"]
        assert retrieved_order["symbol"] == "TCS"
        assert retrieved_order["quantity"] == quantity
    
    @given(
        quantity=st.integers(min_value=1, max_value=1000),
        order_type=st.sampled_from(OrderType),
        order_style=st.sampled_from(OrderStyle),
    )
    def test_order_state_management(self, quantity, order_type, order_style):
        """
        Feature: trading-api-sdk, Property 7: Order State Management
        For any order, it should support all required states and maintain valid state transitions
        """
        price = 100.0 if order_style == OrderStyle.LIMIT else None
        
        order_data = {
            "symbol": "TCS",
            "order_type": order_type.value,
            "order_style": order_style.value,
            "quantity": quantity,
            "price": price
        }
        
        # Place order
        place_response = client.post("/api/v1/orders", json=order_data)
        assert place_response.status_code == 200
        
        placed_order = place_response.json()
        
        # Verify order has valid initial state
        assert placed_order["status"] in ["NEW", "PLACED"]
        
        # Verify all required fields are present
        assert "id" in placed_order
        assert "symbol" in placed_order
        assert "order_type" in placed_order
        assert "order_style" in placed_order
        assert "quantity" in placed_order
        assert "status" in placed_order
        assert "created_at" in placed_order
    
    def test_error_handling_consistency_invalid_order_id(self):
        """
        Feature: trading-api-sdk, Property 13: Error Handling Consistency
        For any invalid request, the system should return descriptive error messages with appropriate HTTP status codes
        """
        # Test with various invalid order IDs (excluding empty string which hits wrong route)
        invalid_ids = ["invalid-id", "12345", "nonexistent-uuid"]
        
        for invalid_id in invalid_ids:
            response = client.get(f"/api/v1/orders/{invalid_id}")
            assert response.status_code == 404
            
            error_response = response.json()
            assert "detail" in error_response
            assert "error" in error_response["detail"]
            assert "code" in error_response["detail"]["error"]
            assert "message" in error_response["detail"]["error"]
            assert error_response["detail"]["error"]["code"] == "ORDER_NOT_FOUND"
    
    @given(
        quantity=st.integers(max_value=0),  # Invalid quantities
    )
    def test_error_handling_consistency_invalid_quantity(self, quantity):
        """
        Feature: trading-api-sdk, Property 13: Error Handling Consistency
        For any invalid request, the system should return descriptive error messages with appropriate HTTP status codes
        """
        order_data = {
            "symbol": "TCS",
            "order_type": "BUY",
            "order_style": "MARKET",
            "quantity": quantity,
            "price": None
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == 422  # Pydantic validation error
        
        error_response = response.json()
        assert "detail" in error_response
    
    def test_error_handling_consistency_limit_without_price(self):
        """
        Feature: trading-api-sdk, Property 13: Error Handling Consistency
        For any invalid request, the system should return descriptive error messages with appropriate HTTP status codes
        """
        order_data = {
            "symbol": "TCS",
            "order_type": "BUY",
            "order_style": "LIMIT",
            "quantity": 100,
            "price": None
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == 400
        
        error_response = response.json()
        assert "detail" in error_response
        assert "error" in error_response["detail"]
        assert error_response["detail"]["error"]["code"] == "VALIDATION_ERROR"
    
    def test_error_handling_consistency_invalid_symbol(self):
        """
        Feature: trading-api-sdk, Property 13: Error Handling Consistency
        For any invalid request, the system should return descriptive error messages with appropriate HTTP status codes
        """
        order_data = {
            "symbol": "INVALID_SYMBOL",
            "order_type": "BUY",
            "order_style": "MARKET",
            "quantity": 100,
            "price": None
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == 400
        
        error_response = response.json()
        assert "detail" in error_response
        assert "error" in error_response["detail"]
        assert error_response["detail"]["error"]["code"] == "VALIDATION_ERROR"