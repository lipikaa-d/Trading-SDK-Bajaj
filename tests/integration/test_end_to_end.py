"""
Integration tests for end-to-end workflows.
Tests complete trading workflows from order placement to portfolio updates.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestEndToEndWorkflows:
    """Test complete trading workflows."""
    
    def test_complete_trading_workflow(self):
        """Test complete workflow: place order → execute → check portfolio."""
        
        # Step 1: Check available instruments
        instruments_response = client.get("/api/v1/instruments")
        assert instruments_response.status_code == 200
        instruments = instruments_response.json()
        assert len(instruments) > 0
        
        # Use first available instrument
        test_symbol = instruments[0]["symbol"]
        
        # Step 2: Check initial portfolio (should be empty)
        portfolio_response = client.get("/api/v1/portfolio")
        assert portfolio_response.status_code == 200
        initial_portfolio = portfolio_response.json()
        
        # Step 3: Place a buy order
        buy_order = {
            "symbol": test_symbol,
            "quantity": 10,
            "order_type": "BUY",
            "order_style": "MARKET"
        }
        
        order_response = client.post("/api/v1/orders", json=buy_order)
        assert order_response.status_code == 201
        order_data = order_response.json()
        
        buy_order_id = order_data["id"]
        assert order_data["symbol"] == test_symbol
        assert order_data["quantity"] == 10
        assert order_data["order_type"] == "BUY"
        assert order_data["status"] == "EXECUTED"  # Market orders execute immediately
        
        # Step 4: Check order status
        order_status_response = client.get(f"/api/v1/orders/{buy_order_id}")
        assert order_status_response.status_code == 200
        order_status = order_status_response.json()
        assert order_status["status"] == "EXECUTED"
        
        # Step 5: Check trades (should have one trade)
        trades_response = client.get("/api/v1/trades")
        assert trades_response.status_code == 200
        trades = trades_response.json()
        assert len(trades) >= 1
        
        # Find our trade
        our_trade = next((t for t in trades if t["order_id"] == buy_order_id), None)
        assert our_trade is not None
        assert our_trade["symbol"] == test_symbol
        assert our_trade["quantity"] == 10
        # Trade doesn't have 'side' field, it's derived from order_type
        
        # Step 6: Check updated portfolio
        updated_portfolio_response = client.get("/api/v1/portfolio")
        assert updated_portfolio_response.status_code == 200
        updated_portfolio = updated_portfolio_response.json()
        
        # Should have position in the symbol we bought
        position = next((p for p in updated_portfolio if p["symbol"] == test_symbol), None)
        assert position is not None
        assert position["quantity"] == 10
        assert float(position["average_price"]) > 0
        assert float(position["current_value"]) > 0
        
        # Step 7: Place a sell order to reduce position
        sell_order = {
            "symbol": test_symbol,
            "quantity": 5,
            "order_type": "SELL",
            "order_style": "MARKET"
        }
        
        sell_response = client.post("/api/v1/orders", json=sell_order)
        assert sell_response.status_code == 201
        sell_data = sell_response.json()
        assert sell_data["status"] == "EXECUTED"
        
        # Step 8: Check final portfolio (should have reduced position)
        final_portfolio_response = client.get("/api/v1/portfolio")
        assert final_portfolio_response.status_code == 200
        final_portfolio = final_portfolio_response.json()
        
        final_position = next((p for p in final_portfolio if p["symbol"] == test_symbol), None)
        assert final_position is not None
        assert final_position["quantity"] == 5  # 10 - 5 = 5
    
    def test_limit_order_workflow(self):
        """Test limit order placement and status tracking."""
        
        # Get instrument for pricing
        instruments_response = client.get("/api/v1/instruments")
        instruments = instruments_response.json()
        test_instrument = instruments[0]
        
        # Place limit order with specific price
        limit_order = {
            "symbol": test_instrument["symbol"],
            "quantity": 5,
            "order_type": "BUY",
            "order_style": "LIMIT",
            "price": float(test_instrument["last_traded_price"]) * 0.95  # Below market price
        }
        
        order_response = client.post("/api/v1/orders", json=limit_order)
        assert order_response.status_code == 201
        order_data = order_response.json()
        
        # Limit order should be placed but not executed
        assert order_data["status"] == "PLACED"
        assert abs(float(order_data["price"]) - limit_order["price"]) < 0.01  # Allow small floating point differences
        
        # Check order status
        order_id = order_data["id"]
        status_response = client.get(f"/api/v1/orders/{order_id}")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["status"] == "PLACED"
    
    def test_multiple_instruments_portfolio(self):
        """Test portfolio with multiple instrument positions."""
        
        instruments_response = client.get("/api/v1/instruments")
        instruments = instruments_response.json()
        
        # Place orders for multiple instruments
        orders_placed = []
        for i, instrument in enumerate(instruments[:3]):  # Use first 3 instruments
            order = {
                "symbol": instrument["symbol"],
                "quantity": (i + 1) * 5,  # Different quantities
                "order_type": "BUY",
                "order_style": "MARKET"
            }
            
            response = client.post("/api/v1/orders", json=order)
            assert response.status_code == 201
            orders_placed.append(response.json())
        
        # Check portfolio has all positions
        portfolio_response = client.get("/api/v1/portfolio")
        assert portfolio_response.status_code == 200
        portfolio = portfolio_response.json()
        
        # Should have at least 3 positions
        assert len(portfolio) >= 3
        
        # Verify each position
        for i, order in enumerate(orders_placed):
            position = next((p for p in portfolio if p["symbol"] == order["symbol"]), None)
            assert position is not None
            assert position["quantity"] >= (i + 1) * 5  # At least what we ordered
    
    def test_error_handling_integration(self):
        """Test error handling across different endpoints."""
        
        # Test invalid instrument
        invalid_order = {
            "symbol": "INVALID_SYMBOL",
            "quantity": 10,
            "order_type": "BUY",
            "order_style": "MARKET"
        }
        
        response = client.post("/api/v1/orders", json=invalid_order)
        assert response.status_code == 404
        error_data = response.json()
        assert error_data["error"]["code"] == "INSTRUMENT_NOT_FOUND"
        
        # Test invalid order ID
        response = client.get("/api/v1/orders/nonexistent")
        assert response.status_code == 404
        error_data = response.json()
        assert error_data["error"]["code"] == "ORDER_NOT_FOUND"
        
        # Test invalid data
        invalid_data = {
            "symbol": "TCS",
            "quantity": -5,
            "order_type": "BUY",
            "order_style": "MARKET"
        }
        
        response = client.post("/api/v1/orders", json=invalid_data)
        assert response.status_code == 422
        error_data = response.json()
        assert error_data["error"]["code"] == "VALIDATION_ERROR"
    
    def test_system_health_and_monitoring(self):
        """Test health check and system monitoring."""
        
        # Test health endpoint
        health_response = client.get("/health")
        assert health_response.status_code == 200
        health_data = health_response.json()
        
        assert health_data["status"] == "healthy"
        assert health_data["service"] == "Trading API SDK"
        assert health_data["version"] == "1.0.0"
        assert "system_stats" in health_data
        assert "components" in health_data
        
        # Verify system stats
        stats = health_data["system_stats"]
        assert "instruments_loaded" in stats
        assert "total_orders" in stats
        assert "total_trades" in stats
        assert "portfolio_positions" in stats
        
        # Verify components status
        components = health_data["components"]
        assert components["storage"] == "operational"
        assert components["order_service"] == "operational"
        assert components["trade_service"] == "operational"
        assert components["portfolio_service"] == "operational"
    
    def test_api_documentation_endpoints(self):
        """Test that API documentation is accessible."""
        
        # Test OpenAPI schema
        docs_response = client.get("/docs")
        assert docs_response.status_code == 200
        
        # Test ReDoc
        redoc_response = client.get("/redoc")
        assert redoc_response.status_code == 200
        
        # Test OpenAPI JSON
        openapi_response = client.get("/openapi.json")
        assert openapi_response.status_code == 200
        openapi_data = openapi_response.json()
        
        assert openapi_data["info"]["title"] == "Trading API SDK"
        assert openapi_data["info"]["version"] == "1.0.0"
        assert "paths" in openapi_data
        
        # Verify key endpoints are documented
        paths = openapi_data["paths"]
        assert "/api/v1/instruments" in paths
        assert "/api/v1/orders" in paths
        assert "/api/v1/trades" in paths
        assert "/api/v1/portfolio" in paths
        assert "/health" in paths