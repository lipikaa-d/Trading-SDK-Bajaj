import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestOrderEndpoints:
    
    def test_place_market_order_success(self):
        order_data = {
            "symbol": "TCS",
            "order_type": "BUY",
            "order_style": "MARKET",
            "quantity": 100,
            "price": None
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == 200
        
        order = response.json()
        assert order["symbol"] == "TCS"
        assert order["order_type"] == "BUY"
        assert order["order_style"] == "MARKET"
        assert order["quantity"] == 100
        assert order["price"] is None
        assert order["status"] == "PLACED"
        assert "id" in order
        assert "created_at" in order
    
    def test_place_limit_order_success(self):
        order_data = {
            "symbol": "INFY",
            "order_type": "SELL",
            "order_style": "LIMIT",
            "quantity": 50,
            "price": 1500.00
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == 200
        
        order = response.json()
        assert order["symbol"] == "INFY"
        assert order["order_type"] == "SELL"
        assert order["order_style"] == "LIMIT"
        assert order["quantity"] == 50
        assert order["price"] == "1500.0"  # Decimal serialized as string
        assert order["status"] == "PLACED"
    
    def test_place_order_invalid_symbol(self):
        order_data = {
            "symbol": "INVALID",
            "order_type": "BUY",
            "order_style": "MARKET",
            "quantity": 100,
            "price": None
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == 400
        
        error = response.json()
        assert "detail" in error
        assert "error" in error["detail"]
        assert error["detail"]["error"]["code"] == "VALIDATION_ERROR"
        assert "not found" in error["detail"]["error"]["message"]
    
    def test_place_limit_order_without_price(self):
        order_data = {
            "symbol": "TCS",
            "order_type": "BUY",
            "order_style": "LIMIT",
            "quantity": 100,
            "price": None
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == 400
        
        error = response.json()
        assert "detail" in error
        assert "error" in error["detail"]
        assert error["detail"]["error"]["code"] == "VALIDATION_ERROR"
        assert "Price is required" in error["detail"]["error"]["message"]
    
    def test_place_order_invalid_quantity(self):
        order_data = {
            "symbol": "TCS",
            "order_type": "BUY",
            "order_style": "MARKET",
            "quantity": 0,
            "price": None
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == 422  # Pydantic validation error
        
        error = response.json()
        assert "detail" in error
    
    def test_get_order_status_success(self):
        # First place an order
        order_data = {
            "symbol": "TCS",
            "order_type": "BUY",
            "order_style": "MARKET",
            "quantity": 100,
            "price": None
        }
        
        place_response = client.post("/api/v1/orders", json=order_data)
        assert place_response.status_code == 200
        
        placed_order = place_response.json()
        order_id = placed_order["id"]
        
        # Get order status
        status_response = client.get(f"/api/v1/orders/{order_id}")
        assert status_response.status_code == 200
        
        retrieved_order = status_response.json()
        assert retrieved_order["id"] == order_id
        assert retrieved_order["symbol"] == "TCS"
        assert retrieved_order["status"] == "PLACED"
    
    def test_get_order_status_not_found(self):
        response = client.get("/api/v1/orders/nonexistent-id")
        assert response.status_code == 404
        
        error = response.json()
        assert "detail" in error
        assert "error" in error["detail"]
        assert error["detail"]["error"]["code"] == "ORDER_NOT_FOUND"
        assert "not found" in error["detail"]["error"]["message"]
    
    def test_place_order_malformed_json(self):
        # Test with missing required fields
        order_data = {
            "symbol": "TCS",
            "order_type": "BUY"
            # Missing order_style and quantity
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == 422  # Pydantic validation error
        
        error = response.json()
        assert "detail" in error
    
    def test_place_order_invalid_enum_values(self):
        order_data = {
            "symbol": "TCS",
            "order_type": "INVALID_TYPE",
            "order_style": "MARKET",
            "quantity": 100,
            "price": None
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == 422  # Pydantic validation error
        
        error = response.json()
        assert "detail" in error