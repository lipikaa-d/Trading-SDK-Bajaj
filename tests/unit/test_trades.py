import pytest
from decimal import Decimal
from app.services.trade_service import TradeService
from app.models import Order, OrderType, OrderStyle, OrderStatus
from app.storage import InMemoryStorage


class TestTradeService:
    
    def setup_method(self):
        self.storage = InMemoryStorage()
        self.trade_service = TradeService()
        self.trade_service.storage = self.storage
    
    def test_execute_market_order_buy(self):
        order = Order.create("TCS", OrderType.BUY, OrderStyle.MARKET, 100)
        order.status = OrderStatus.PLACED
        self.storage.save_order(order)
        
        trade = self.trade_service.execute_market_order(order)
        
        assert trade is not None
        assert trade.order_id == order.id
        assert trade.symbol == "TCS"
        assert trade.quantity == 100
        assert trade.price == Decimal("3450.25")  # TCS market price
        
        # Verify order status updated
        updated_order = self.storage.get_order(order.id)
        assert updated_order.status == OrderStatus.EXECUTED
        
        # Verify portfolio updated
        holding = self.storage.get_portfolio_holding("TCS")
        assert holding is not None
        assert holding.quantity == 100
    
    def test_execute_market_order_sell(self):
        # First add some holdings
        self.storage.update_portfolio_position("INFY", 200, Decimal("1500.00"))
        
        order = Order.create("INFY", OrderType.SELL, OrderStyle.MARKET, 50)
        order.status = OrderStatus.PLACED
        self.storage.save_order(order)
        
        trade = self.trade_service.execute_market_order(order)
        
        assert trade is not None
        assert trade.symbol == "INFY"
        assert trade.quantity == 50
        assert trade.price == Decimal("1520.40")  # INFY market price
        
        # Verify portfolio updated (200 - 50 = 150)
        holding = self.storage.get_portfolio_holding("INFY")
        assert holding.quantity == 150
    
    def test_execute_market_order_invalid_style(self):
        order = Order.create("TCS", OrderType.BUY, OrderStyle.LIMIT, 100, Decimal("3400.00"))
        
        with pytest.raises(ValueError, match="Only market orders can be executed immediately"):
            self.trade_service.execute_market_order(order)
    
    def test_execute_market_order_invalid_symbol(self):
        order = Order.create("INVALID", OrderType.BUY, OrderStyle.MARKET, 100)
        order.status = OrderStatus.PLACED
        self.storage.save_order(order)
        
        with pytest.raises(ValueError, match="Instrument INVALID not found"):
            self.trade_service.execute_market_order(order)
    
    def test_execute_limit_order_buy_executable(self):
        order = Order.create("TCS", OrderType.BUY, OrderStyle.LIMIT, 100, Decimal("3500.00"))
        order.status = OrderStatus.PLACED
        self.storage.save_order(order)
        
        # Market price is 3450.25, limit is 3500.00, should execute
        trade = self.trade_service.execute_limit_order(order, Decimal("3450.25"))
        
        assert trade is not None
        assert trade.price == Decimal("3500.00")  # Executed at limit price
        
        # Verify order status updated
        updated_order = self.storage.get_order(order.id)
        assert updated_order.status == OrderStatus.EXECUTED
    
    def test_execute_limit_order_buy_not_executable(self):
        order = Order.create("TCS", OrderType.BUY, OrderStyle.LIMIT, 100, Decimal("3400.00"))
        order.status = OrderStatus.PLACED
        self.storage.save_order(order)
        
        # Market price is 3450.25, limit is 3400.00, should not execute
        trade = self.trade_service.execute_limit_order(order, Decimal("3450.25"))
        
        assert trade is None
        
        # Verify order status unchanged
        updated_order = self.storage.get_order(order.id)
        assert updated_order.status == OrderStatus.PLACED
    
    def test_execute_limit_order_sell_executable(self):
        order = Order.create("TCS", OrderType.SELL, OrderStyle.LIMIT, 100, Decimal("3400.00"))
        order.status = OrderStatus.PLACED
        self.storage.save_order(order)
        
        # Market price is 3450.25, limit is 3400.00, should execute
        trade = self.trade_service.execute_limit_order(order, Decimal("3450.25"))
        
        assert trade is not None
        assert trade.price == Decimal("3400.00")  # Executed at limit price
    
    def test_execute_limit_order_sell_not_executable(self):
        order = Order.create("TCS", OrderType.SELL, OrderStyle.LIMIT, 100, Decimal("3500.00"))
        order.status = OrderStatus.PLACED
        self.storage.save_order(order)
        
        # Market price is 3450.25, limit is 3500.00, should not execute
        trade = self.trade_service.execute_limit_order(order, Decimal("3450.25"))
        
        assert trade is None
    
    def test_get_all_trades(self):
        # Execute some orders to create trades
        order1 = Order.create("TCS", OrderType.BUY, OrderStyle.MARKET, 100)
        order1.status = OrderStatus.PLACED
        self.storage.save_order(order1)
        
        order2 = Order.create("INFY", OrderType.BUY, OrderStyle.MARKET, 50)
        order2.status = OrderStatus.PLACED
        self.storage.save_order(order2)
        
        trade1 = self.trade_service.execute_market_order(order1)
        trade2 = self.trade_service.execute_market_order(order2)
        
        all_trades = self.trade_service.get_all_trades()
        
        assert len(all_trades) == 2
        trade_ids = [trade.id for trade in all_trades]
        assert trade1.id in trade_ids
        assert trade2.id in trade_ids
    
    def test_get_trades_for_symbol(self):
        # Execute orders for different symbols
        tcs_order = Order.create("TCS", OrderType.BUY, OrderStyle.MARKET, 100)
        tcs_order.status = OrderStatus.PLACED
        self.storage.save_order(tcs_order)
        
        infy_order = Order.create("INFY", OrderType.BUY, OrderStyle.MARKET, 50)
        infy_order.status = OrderStatus.PLACED
        self.storage.save_order(infy_order)
        
        tcs_trade = self.trade_service.execute_market_order(tcs_order)
        infy_trade = self.trade_service.execute_market_order(infy_order)
        
        tcs_trades = self.trade_service.get_trades_for_symbol("TCS")
        infy_trades = self.trade_service.get_trades_for_symbol("INFY")
        
        assert len(tcs_trades) == 1
        assert len(infy_trades) == 1
        assert tcs_trades[0].id == tcs_trade.id
        assert infy_trades[0].id == infy_trade.id
    
    def test_simulate_market_execution(self):
        # Create multiple market orders
        order1 = Order.create("TCS", OrderType.BUY, OrderStyle.MARKET, 100)
        order1.status = OrderStatus.PLACED
        self.storage.save_order(order1)
        
        order2 = Order.create("INFY", OrderType.BUY, OrderStyle.MARKET, 50)
        order2.status = OrderStatus.PLACED
        self.storage.save_order(order2)
        
        # Create a limit order (should not be executed)
        limit_order = Order.create("RELIANCE", OrderType.BUY, OrderStyle.LIMIT, 25, Decimal("2800.00"))
        limit_order.status = OrderStatus.PLACED
        self.storage.save_order(limit_order)
        
        executed_trades = self.trade_service.simulate_market_execution()
        
        assert len(executed_trades) == 2  # Only market orders executed
        
        # Verify all market orders are now EXECUTED
        updated_order1 = self.storage.get_order(order1.id)
        updated_order2 = self.storage.get_order(order2.id)
        updated_limit_order = self.storage.get_order(limit_order.id)
        
        assert updated_order1.status == OrderStatus.EXECUTED
        assert updated_order2.status == OrderStatus.EXECUTED
        assert updated_limit_order.status == OrderStatus.PLACED  # Unchanged