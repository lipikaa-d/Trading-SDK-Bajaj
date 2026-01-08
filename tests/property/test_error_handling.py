import pytest
from hypothesis import given, strategies as st
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestErrorHandlingProperties:
    
    @given(
        invalid_quantity=st.integers(max_value=0),
    )
    def test_error_handling_consistency_invalid_input(self, invalid_quantity):
        """
        Feature: trading-api-sdk, Property 13: Error Handling Consistency
        For any invalid request, the system should return descriptive error messages with appropriate HTTP status codes
        """
        order_data = {
            "symbol": "TCS",
            "order_type": "BUY",
            "order_style": "MARKET",
            "quantity": invalid_quantity,
            "price": None
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        
        # Should return validation error
        assert response.status_code == 422
        
        error_response = response.json()
        assert "error" in error_response
        assert "code" in error_response["error"]
        assert "message" in error_response["error"]
        assert error_response["error"]["code"] == "VALIDATION_ERROR"
        assert isinstance(error_response["error"]["message"], str)
        assert len(error_response["error"]["message"]) > 0
    
    @given(
        invalid_symbol=st.text(min_size=1, max_size=20).filter(
            lambda x: x not in ["TCS", "INFY", "RELIANCE", "HDFC", "ICICIBANK"]
        ),
        quantity=st.integers(min_value=1, max_value=1000),
    )
    def test_error_handling_consistency_invalid_symbol(self, invalid_symbol, quantity):
        """
        Feature: trading-api-sdk, Property 13: Error Handling Consistency
        For any invalid request, the system should return descriptive error messages with appropriate HTTP status codes
        """
        order_data = {
            "symbol": invalid_symbol,
            "order_type": "BUY",
            "order_style": "MARKET",
            "quantity": quantity,
            "price": None
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        
        # Should return instrument not found error
        assert response.status_code == 404
        
        error_response = response.json()
        assert "error" in error_response
        assert "code" in error_response["error"]
        assert "message" in error_response["error"]
        assert error_response["error"]["code"] == "INSTRUMENT_NOT_FOUND"
        assert invalid_symbol in error_response["error"]["message"]
    
    @given(
        invalid_order_id=st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
            min_size=1, 
            max_size=20
        ),
    )
    def test_error_handling_consistency_invalid_order_id(self, invalid_order_id):
        """
        Feature: trading-api-sdk, Property 13: Error Handling Consistency
        For any invalid request, the system should return descriptive error messages with appropriate HTTP status codes
        """
        response = client.get(f"/api/v1/orders/{invalid_order_id}")
        
        # Should return order not found error
        assert response.status_code == 404
        
        error_response = response.json()
        assert "error" in error_response
        assert "code" in error_response["error"]
        assert "message" in error_response["error"]
        assert error_response["error"]["code"] == "ORDER_NOT_FOUND"
        assert "not found" in error_response["error"]["message"].lower()
    
    @given(
        quantity=st.integers(min_value=1, max_value=1000),
    )
    def test_input_validation_limit_orders(self, quantity):
        """
        Feature: trading-api-sdk, Property 14: Input Validation
        For any API endpoint, all input parameters should be validated before processing
        """
        # Test limit order without price
        order_data = {
            "symbol": "TCS",
            "order_type": "BUY",
            "order_style": "LIMIT",
            "quantity": quantity,
            "price": None
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        
        # Should return validation error
        assert response.status_code == 400
        
        error_response = response.json()
        assert "error" in error_response
        assert error_response["error"]["code"] == "VALIDATION_ERROR"
        assert "price" in error_response["error"]["message"].lower()
    
    def test_json_response_format_success(self):
        """
        Feature: trading-api-sdk, Property 15: JSON Response Format
        For any API response, it should use JSON format with proper content-type headers
        """
        # Test successful response
        response = client.get("/api/v1/instruments")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        # Should be valid JSON
        data = response.json()
        assert isinstance(data, list)
    
    def test_json_response_format_error(self):
        """
        Feature: trading-api-sdk, Property 15: JSON Response Format
        For any API response, it should use JSON format with proper content-type headers
        """
        # Test error response
        response = client.get("/api/v1/orders/invalid-id")
        
        assert response.status_code == 404
        assert response.headers["content-type"] == "application/json"
        
        # Should be valid JSON with error structure
        data = response.json()
        assert isinstance(data, dict)
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]
    
    def test_input_validation_malformed_json(self):
        """
        Feature: trading-api-sdk, Property 14: Input Validation
        Test validation of malformed requests
        """
        # Test with missing required fields
        incomplete_order = {
            "symbol": "TCS",
            "order_type": "BUY"
            # Missing order_style and quantity
        }
        
        response = client.post("/api/v1/orders", json=incomplete_order)
        
        assert response.status_code == 422
        
        error_response = response.json()
        assert "error" in error_response
        assert error_response["error"]["code"] == "VALIDATION_ERROR"
        assert "details" in error_response["error"]
        assert "validation_errors" in error_response["error"]["details"]
    
    def test_input_validation_invalid_enum_values(self):
        """
        Feature: trading-api-sdk, Property 14: Input Validation
        Test validation of invalid enum values
        """
        order_data = {
            "symbol": "TCS",
            "order_type": "INVALID_TYPE",
            "order_style": "MARKET",
            "quantity": 100,
            "price": None
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        
        assert response.status_code == 422
        
        error_response = response.json()
        assert "error" in error_response
        assert error_response["error"]["code"] == "VALIDATION_ERROR"
    
    def test_error_message_descriptiveness(self):
        """
        Test that error messages are descriptive and helpful
        """
        # Test various error scenarios
        error_scenarios = [
            {
                "data": {"symbol": "TCS", "order_type": "BUY", "order_style": "MARKET", "quantity": 0},
                "expected_status": 422,
                "expected_code": "VALIDATION_ERROR"
            },
            {
                "data": {"symbol": "INVALID", "order_type": "BUY", "order_style": "MARKET", "quantity": 100},
                "expected_status": 404,
                "expected_code": "INSTRUMENT_NOT_FOUND"
            },
            {
                "data": {"symbol": "TCS", "order_type": "BUY", "order_style": "LIMIT", "quantity": 100, "price": None},
                "expected_status": 400,
                "expected_code": "VALIDATION_ERROR"
            }
        ]
        
        for scenario in error_scenarios:
            response = client.post("/api/v1/orders", json=scenario["data"])
            
            assert response.status_code == scenario["expected_status"]
            
            error_response = response.json()
            assert "error" in error_response
            assert error_response["error"]["code"] == scenario["expected_code"]
            
            # Error message should be descriptive (not empty, not generic)
            message = error_response["error"]["message"]
            assert isinstance(message, str)
            assert len(message) > 10  # Should be reasonably descriptive
            assert message != "An error occurred"  # Should not be generic