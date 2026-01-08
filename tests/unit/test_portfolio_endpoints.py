import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.portfolio_service import portfolio_service
from app.services.order_service import order_service
from app.services.trade_service import trade_service
from app.models import PortfolioHolding
from decimal import Decimal


client = TestClient(app)


class TestPortfolioEndpoints:
    
    def test_get_portfolio_empty(self):
        """Test that empty portfolio is handled gracefully"""
        response = client.get("/api/v1/portfolio")
        assert response.status_code == 200
        
        portfolio = response.json()
        assert isinstance(portfolio, list)
        # Note: portfolio might not be empty if other tests have run
        # This test mainly verifies the endpoint works and returns a list
    
    def test_get_portfolio_with_holdings(self):
        """Test portfolio retrieval with actual holdings"""
        # Create some holdings by executing trades
        buy_order_data = {
            "symbol": "TCS",
            "order_type": "BUY",
            "order_style": "MARKET",
            "quantity": 100,
            "price": None
        }
        
        # Place and execute order
        place_response = client.post("/api/v1/orders", json=buy_order_data)
        assert place_response.status_code == 200
        
        placed_order_data = place_response.json()
        order = order_service.get_order_status(placed_order_data["id"])
        trade = trade_service.execute_market_order(order)
        
        # Get portfolio
        portfolio_response = client.get("/api/v1/portfolio")
        assert portfolio_response.status_code == 200
        
        holdings = portfolio_response.json()
        assert len(holdings) >= 1
        
        # Find our TCS holding
        tcs_holding = None
        for holding in holdings:
            if holding["symbol"] == "TCS":
                tcs_holding = holding
                break
        
        assert tcs_holding is not None
        assert tcs_holding["quantity"] >= 100  # At least our 100 shares
        assert tcs_holding["average_price"] == "3450.25"  # TCS market price
        assert "current_value" in tcs_holding
    
    def test_get_portfolio_response_structure(self):
        """Test that portfolio response has correct structure"""
        # Create a holding first
        order_data = {
            "symbol": "INFY",
            "order_type": "BUY",
            "order_style": "MARKET",
            "quantity": 25,
            "price": None
        }
        
        place_response = client.post("/api/v1/orders", json=order_data)
        placed_order = place_response.json()
        
        # Execute order
        order = order_service.get_order_status(placed_order["id"])
        trade_service.execute_market_order(order)
        
        # Get portfolio
        response = client.get("/api/v1/portfolio")
        assert response.status_code == 200
        
        holdings = response.json()
        if holdings:  # If we have holdings
            holding = holdings[-1]  # Get the last holding (most recent)
            
            # Verify all required fields are present
            required_fields = ["symbol", "quantity", "average_price", "current_value"]
            for field in required_fields:
                assert field in holding, f"Missing field: {field}"
            
            # Verify field types
            assert isinstance(holding["symbol"], str)
            assert isinstance(holding["quantity"], int)
            assert isinstance(holding["average_price"], str)  # Decimal serialized as string
            assert isinstance(holding["current_value"], str)  # Decimal serialized as string
    
    def test_get_portfolio_multiple_holdings(self):
        """Test retrieving portfolio with multiple holdings"""
        initial_response = client.get("/api/v1/portfolio")
        initial_holdings = initial_response.json()
        initial_symbols = [h["symbol"] for h in initial_holdings]
        
        # Create holdings for symbols not already in portfolio
        new_symbols = []
        test_symbols = ["HDFC", "ICICIBANK"]  # Use different symbols
        
        for symbol in test_symbols:
            if symbol not in initial_symbols:
                new_symbols.append(symbol)
                
                order_data = {
                    "symbol": symbol,
                    "order_type": "BUY",
                    "order_style": "MARKET",
                    "quantity": 10,
                    "price": None
                }
                
                # Place and execute order
                place_response = client.post("/api/v1/orders", json=order_data)
                placed_order = place_response.json()
                
                order = order_service.get_order_status(placed_order["id"])
                trade_service.execute_market_order(order)
        
        # Get portfolio
        response = client.get("/api/v1/portfolio")
        assert response.status_code == 200
        
        holdings = response.json()
        portfolio_symbols = [h["symbol"] for h in holdings]
        
        # Verify our new symbols are in the portfolio
        for symbol in new_symbols:
            assert symbol in portfolio_symbols
    
    def test_get_portfolio_current_value_calculation(self):
        """Test that current values are calculated correctly"""
        # Create a holding
        order_data = {
            "symbol": "TCS",
            "order_type": "BUY",
            "order_style": "MARKET",
            "quantity": 50,
            "price": None
        }
        
        place_response = client.post("/api/v1/orders", json=order_data)
        placed_order = place_response.json()
        
        order = order_service.get_order_status(placed_order["id"])
        trade = trade_service.execute_market_order(order)
        
        # Get portfolio
        response = client.get("/api/v1/portfolio")
        holdings = response.json()
        
        # Find TCS holding
        tcs_holding = None
        for holding in holdings:
            if holding["symbol"] == "TCS":
                tcs_holding = holding
                break
        
        assert tcs_holding is not None
        
        # Verify current value calculation
        quantity = tcs_holding["quantity"]
        current_value = Decimal(tcs_holding["current_value"])
        market_price = Decimal("3450.25")  # TCS market price
        
        # Current value should be based on market price
        # Note: quantity might be more than 50 if other tests have run
        expected_value = quantity * market_price
        assert current_value == expected_value
    
    def test_get_portfolio_buy_and_sell_positions(self):
        """Test portfolio with both buy and sell transactions"""
        # First buy some shares
        buy_order_data = {
            "symbol": "TCS",
            "order_type": "BUY",
            "order_style": "MARKET",
            "quantity": 100,
            "price": None
        }
        
        buy_response = client.post("/api/v1/orders", json=buy_order_data)
        buy_order = order_service.get_order_status(buy_response.json()["id"])
        trade_service.execute_market_order(buy_order)
        
        # Then sell some shares
        sell_order_data = {
            "symbol": "TCS",
            "order_type": "SELL",
            "order_style": "MARKET",
            "quantity": 30,
            "price": None
        }
        
        sell_response = client.post("/api/v1/orders", json=sell_order_data)
        sell_order = order_service.get_order_status(sell_response.json()["id"])
        trade_service.execute_market_order(sell_order)
        
        # Get portfolio
        response = client.get("/api/v1/portfolio")
        holdings = response.json()
        
        # Find TCS holding
        tcs_holding = None
        for holding in holdings:
            if holding["symbol"] == "TCS":
                tcs_holding = holding
                break
        
        assert tcs_holding is not None
        # Should have net position (buy - sell, plus any from other tests)
        assert tcs_holding["quantity"] > 0
    
    def test_get_portfolio_empty_after_full_sell(self):
        """Test portfolio behavior when all shares are sold"""
        # Check current HDFC holdings
        initial_response = client.get("/api/v1/portfolio")
        initial_holdings = initial_response.json()
        
        hdfc_initial = None
        for holding in initial_holdings:
            if holding["symbol"] == "HDFC":
                hdfc_initial = holding
                break
        
        initial_quantity = hdfc_initial["quantity"] if hdfc_initial else 0
        
        # Buy some additional shares
        buy_quantity = 20
        buy_order_data = {
            "symbol": "HDFC",
            "order_type": "BUY",
            "order_style": "MARKET",
            "quantity": buy_quantity,
            "price": None
        }
        
        buy_response = client.post("/api/v1/orders", json=buy_order_data)
        buy_order = order_service.get_order_status(buy_response.json()["id"])
        trade_service.execute_market_order(buy_order)
        
        # Sell ALL shares (initial + bought)
        total_quantity = initial_quantity + buy_quantity
        sell_order_data = {
            "symbol": "HDFC",
            "order_type": "SELL",
            "order_style": "MARKET",
            "quantity": total_quantity,
            "price": None
        }
        
        sell_response = client.post("/api/v1/orders", json=sell_order_data)
        sell_order = order_service.get_order_status(sell_response.json()["id"])
        trade_service.execute_market_order(sell_order)
        
        # Get portfolio
        response = client.get("/api/v1/portfolio")
        assert response.status_code == 200
        
        holdings = response.json()
        
        # HDFC should not be in portfolio (or have 0 quantity)
        hdfc_holding = None
        for holding in holdings:
            if holding["symbol"] == "HDFC":
                hdfc_holding = holding
                break
        
        # Either no HDFC holding or quantity is 0
        assert hdfc_holding is None or hdfc_holding["quantity"] == 0