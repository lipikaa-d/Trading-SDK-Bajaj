import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.trade_service import trade_service
from app.services.order_service import order_service
from app.models import OrderType, OrderStyle


client = TestClient(app)


class TestTradeEndpoints:
    
    def test_get_trades_empty_list(self):
        """Test that empty trade list is handled gracefully"""
        response = client.get("/api/v1/trades")
        assert response.status_code == 200
        
        trades = response.json()
        assert isinstance(trades, list)
        # Note: trades might not be empty if other tests have run
        # This test mainly verifies the endpoint works and returns a list
    
    def test_get_trades_with_data(self):
        """Test trade retrieval with actual trade data"""
        # Place and execute an order to create a trade
        order_data = {
            "symbol": "TCS",
            "order_type": "BUY",
            "order_style": "MARKET",
            "quantity": 100,
            "price": None
        }
        
        # Place order
        place_response = client.post("/api/v1/orders", json=order_data)
        assert place_response.status_code == 200
        
        placed_order_data = place_response.json()
        order_id = placed_order_data["id"]
        
        # Execute the order to create a trade
        order = order_service.get_order_status(order_id)
        trade = trade_service.execute_market_order(order)
        
        # Get trades
        trades_response = client.get("/api/v1/trades")
        assert trades_response.status_code == 200
        
        trades = trades_response.json()
        assert len(trades) >= 1
        
        # Find our trade
        our_trade = None
        for t in trades:
            if t["id"] == trade.id:
                our_trade = t
                break
        
        assert our_trade is not None
        assert our_trade["order_id"] == order_id
        assert our_trade["symbol"] == "TCS"
        assert our_trade["quantity"] == 100
        assert our_trade["price"] == "3450.25"  # TCS market price
        assert "executed_at" in our_trade
    
    def test_get_trades_response_structure(self):
        """Test that trade response has correct structure"""
        # Create a trade first
        order_data = {
            "symbol": "INFY",
            "order_type": "SELL",
            "order_style": "MARKET",
            "quantity": 50,
            "price": None
        }
        
        place_response = client.post("/api/v1/orders", json=order_data)
        placed_order = place_response.json()
        
        # Execute order
        order = order_service.get_order_status(placed_order["id"])
        trade_service.execute_market_order(order)
        
        # Get trades
        response = client.get("/api/v1/trades")
        assert response.status_code == 200
        
        trades = response.json()
        if trades:  # If we have trades
            trade = trades[-1]  # Get the last trade (most recent)
            
            # Verify all required fields are present
            required_fields = ["id", "order_id", "symbol", "quantity", "price", "executed_at"]
            for field in required_fields:
                assert field in trade, f"Missing field: {field}"
            
            # Verify field types
            assert isinstance(trade["id"], str)
            assert isinstance(trade["order_id"], str)
            assert isinstance(trade["symbol"], str)
            assert isinstance(trade["quantity"], int)
            assert isinstance(trade["price"], str)  # Decimal serialized as string
            assert isinstance(trade["executed_at"], str)  # DateTime serialized as string
    
    def test_get_trades_multiple_trades(self):
        """Test retrieving multiple trades"""
        initial_response = client.get("/api/v1/trades")
        initial_count = len(initial_response.json())
        
        # Create multiple trades
        symbols = ["TCS", "INFY", "RELIANCE"]
        trade_ids = []
        
        for symbol in symbols:
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
            trade = trade_service.execute_market_order(order)
            trade_ids.append(trade.id)
        
        # Get all trades
        response = client.get("/api/v1/trades")
        assert response.status_code == 200
        
        trades = response.json()
        assert len(trades) >= initial_count + 3
        
        # Verify our trades are in the response
        response_trade_ids = [t["id"] for t in trades]
        for trade_id in trade_ids:
            assert trade_id in response_trade_ids
    
    def test_get_trades_different_order_types(self):
        """Test trades from different order types"""
        # Create BUY trade
        buy_order_data = {
            "symbol": "TCS",
            "order_type": "BUY",
            "order_style": "MARKET",
            "quantity": 25,
            "price": None
        }
        
        buy_response = client.post("/api/v1/orders", json=buy_order_data)
        buy_order = order_service.get_order_status(buy_response.json()["id"])
        buy_trade = trade_service.execute_market_order(buy_order)
        
        # Create SELL trade (need to have holdings first)
        # The execute_market_order for BUY above should have created holdings
        sell_order_data = {
            "symbol": "TCS",
            "order_type": "SELL",
            "order_style": "MARKET",
            "quantity": 10,
            "price": None
        }
        
        sell_response = client.post("/api/v1/orders", json=sell_order_data)
        sell_order = order_service.get_order_status(sell_response.json()["id"])
        sell_trade = trade_service.execute_market_order(sell_order)
        
        # Get trades
        response = client.get("/api/v1/trades")
        trades = response.json()
        
        # Find our trades
        our_trades = [t for t in trades if t["id"] in [buy_trade.id, sell_trade.id]]
        assert len(our_trades) == 2
        
        # Both should be for TCS symbol
        for trade in our_trades:
            assert trade["symbol"] == "TCS"