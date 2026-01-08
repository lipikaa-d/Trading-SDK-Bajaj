"""
Unit tests for error scenarios and edge cases.
Tests specific error conditions and HTTP status codes.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestErrorScenarios:
    """Test various error conditions and status codes."""
    
    def test_order_not_found_404(self):
        """Test that non-existent order returns 404."""
        response = client.get("/api/v1/orders/nonexistent123")
        
        assert response.status_code == 404
        error_data = response.json()
        assert error_data["error"]["code"] == "ORDER_NOT_FOUND"
        assert "not found" in error_data["error"]["message"].lower()
    
    def test_invalid_order_data_422(self):
        """Test that invalid order data returns 422."""
        invalid_order = {
            "symbol": "INVALID",
            "quantity": -5,  # Invalid negative quantity
            "order_type": "BUY",
            "order_style": "MARKET"
        }
        
        response = client.post("/api/v1/orders", json=invalid_order)
        
        assert response.status_code == 422
        error_data = response.json()
        assert "error" in error_data
        assert error_data["error"]["code"] == "VALIDATION_ERROR"
    
    def test_missing_price_for_limit_order_400(self):
        """Test that LIMIT order without price returns 400."""
        limit_order = {
            "symbol": "TCS",
            "quantity": 10,
            "order_type": "BUY",
            "order_style": "LIMIT"
            # Missing price field
        }
        
        response = client.post("/api/v1/orders", json=limit_order)
        
        assert response.status_code == 400
        error_data = response.json()
        assert error_data["error"]["code"] == "VALIDATION_ERROR"
        assert "price" in error_data["error"]["message"].lower()
    
    def test_invalid_symbol_400(self):
        """Test that invalid symbol returns 404."""
        order = {
            "symbol": "NONEXISTENT",
            "quantity": 10,
            "order_type": "BUY",
            "order_style": "MARKET"
        }
        
        response = client.post("/api/v1/orders", json=order)
        
        assert response.status_code == 404
        error_data = response.json()
        assert error_data["error"]["code"] == "INSTRUMENT_NOT_FOUND"
        assert "instrument" in error_data["error"]["message"].lower()
    
    def test_zero_quantity_422(self):
        """Test that zero quantity returns 422."""
        order = {
            "symbol": "TCS",
            "quantity": 0,
            "order_type": "BUY",
            "order_style": "MARKET"
        }
        
        response = client.post("/api/v1/orders", json=order)
        
        assert response.status_code == 422
        error_data = response.json()
        assert error_data["error"]["code"] == "VALIDATION_ERROR"
        assert "validation" in error_data["error"]["message"].lower()
    
    def test_negative_price_400(self):
        """Test that negative price returns 400."""
        order = {
            "symbol": "TCS",
            "quantity": 10,
            "order_type": "BUY",
            "order_style": "LIMIT",
            "price": -100.0
        }
        
        response = client.post("/api/v1/orders", json=order)
        
        assert response.status_code == 400
        error_data = response.json()
        assert error_data["error"]["code"] == "VALIDATION_ERROR"
        assert "price" in error_data["error"]["message"].lower()
    
    def test_malformed_json_422(self):
        """Test that malformed JSON returns 422."""
        response = client.post(
            "/api/v1/orders",
            data='{"symbol": "TCS", "quantity":}',  # Invalid JSON
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_invalid_order_type_422(self):
        """Test that invalid order type returns 422."""
        order = {
            "symbol": "TCS",
            "quantity": 10,
            "order_type": "INVALID_TYPE",
            "order_style": "MARKET"
        }
        
        response = client.post("/api/v1/orders", json=order)
        
        assert response.status_code == 422
        error_data = response.json()
        assert "error" in error_data
        assert error_data["error"]["code"] == "VALIDATION_ERROR"
    
    def test_invalid_order_style_422(self):
        """Test that invalid order style returns 422."""
        order = {
            "symbol": "TCS",
            "quantity": 10,
            "order_type": "BUY",
            "order_style": "INVALID_STYLE"
        }
        
        response = client.post("/api/v1/orders", json=order)
        
        assert response.status_code == 422
        error_data = response.json()
        assert "error" in error_data
        assert error_data["error"]["code"] == "VALIDATION_ERROR"
    
    def test_missing_required_fields_422(self):
        """Test that missing required fields return 422."""
        incomplete_order = {
            "symbol": "TCS"
            # Missing quantity, order_type, order_style
        }
        
        response = client.post("/api/v1/orders", json=incomplete_order)
        
        assert response.status_code == 422
        error_data = response.json()
        assert "error" in error_data
        assert error_data["error"]["code"] == "VALIDATION_ERROR"
    
    def test_empty_request_body_422(self):
        """Test that empty request body returns 422."""
        response = client.post("/api/v1/orders", json={})
        
        assert response.status_code == 422
        error_data = response.json()
        assert "error" in error_data
        assert error_data["error"]["code"] == "VALIDATION_ERROR"
    
    def test_invalid_content_type_422(self):
        """Test that invalid content type returns 422."""
        response = client.post(
            "/api/v1/orders",
            data="not json data",
            headers={"Content-Type": "text/plain"}
        )
        
        assert response.status_code == 422
    
    def test_method_not_allowed_405(self):
        """Test that wrong HTTP method returns 405."""
        response = client.put("/api/v1/orders")
        
        assert response.status_code == 405
    
    def test_not_found_endpoint_404(self):
        """Test that non-existent endpoint returns 404."""
        response = client.get("/api/v1/nonexistent")
        
        assert response.status_code == 404
    
    def test_error_response_format_consistency(self):
        """Test that all error responses have consistent format."""
        # Test various error scenarios
        test_cases = [
            ("/api/v1/orders/nonexistent", "get"),
            ("/api/v1/orders", "put"),  # Method not allowed
        ]
        
        for endpoint, method in test_cases:
            if method == "get":
                response = client.get(endpoint)
            elif method == "put":
                response = client.put(endpoint)
            
            # All errors should be JSON
            assert response.headers.get("content-type") == "application/json"
            
            # Check response structure for custom errors (not FastAPI validation errors)
            if response.status_code in [400, 404]:
                error_data = response.json()
                assert "error" in error_data
                assert "code" in error_data["error"]
                assert "message" in error_data["error"]
                assert isinstance(error_data["error"]["code"], str)
                assert isinstance(error_data["error"]["message"], str)