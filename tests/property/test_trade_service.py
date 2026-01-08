import pytest
from hypothesis import given, strategies as st
from decimal import Decimal
from app.services.trade_service import TradeService
from app.models import Order, OrderType, OrderStyle, OrderStatus
from app.storage import InMemoryStorage


class TestTradeServiceProperties:
    
    def setup_method(self):
        self.storage = InMemoryStorage()
        self.trade_service = TradeService()
        self.trade_service.storage = self.storage
    
    @given(
        quantity=st.integers(min_value=1, max_value=1000),
        order_type=st.sampled_from(OrderType),
    )
    def test_trade_data_completeness(self, quantity, order_type):
        """
        Feature: trading-api-sdk, Property 8: Trade Data Completeness
        For any trade returned by the system, it should contain symbol, quantity, price, and execution_time fields
        """
        # Create and execute a market order
        order = Order.create("TCS", order_type, OrderStyle.MARKET, quantity)
        order.status = OrderStatus.PLACED
        self.storage.save_order(order)
        
        trade = self.trade_service.execute_market_order(order)
        
        # Verify trade has all required fields
        assert hasattr(trade, 'id')
        assert hasattr(trade, 'order_id')
        assert hasattr(trade, 'symbol')
        assert hasattr(trade, 'quantity')
        assert hasattr(trade, 'price')
        assert hasattr(trade, 'executed_at')
        
        # Verify field values are not None
        assert trade.id is not None
        assert trade.order_id is not None
        assert trade.symbol is not None
        assert trade.quantity is not None
        assert trade.price is not None
        assert trade.executed_at is not None
        
        # Verify field types
        assert isinstance(trade.id, str)
        assert isinstance(trade.order_id, str)
        assert isinstance(trade.symbol, str)
        assert isinstance(trade.quantity, int)
        assert isinstance(trade.price, Decimal)
        
        # Verify trade data matches order
        assert trade.order_id == order.id
        assert trade.symbol == order.symbol
        assert trade.quantity == order.quantity
    
    @given(
        quantity=st.integers(min_value=1, max_value=1000),
        order_type=st.sampled_from(OrderType),
    )
    def test_trade_persistence(self, quantity, order_type):
        """
        Feature: trading-api-sdk, Property 9: Trade Persistence
        For any executed trade, it should remain accessible in the trade history for the session duration
        """
        # Create and execute multiple orders
        orders = []
        trade_ids = []
        
        for i in range(3):
            order = Order.create("TCS", order_type, OrderStyle.MARKET, quantity + i)
            order.status = OrderStatus.PLACED
            self.storage.save_order(order)
            orders.append(order)
            
            trade = self.trade_service.execute_market_order(order)
            trade_ids.append(trade.id)
        
        # Verify all trades are accessible
        all_trades = self.trade_service.get_all_trades()
        retrieved_trade_ids = [trade.id for trade in all_trades]
        
        for trade_id in trade_ids:
            assert trade_id in retrieved_trade_ids
            
            # Verify individual trade retrieval
            individual_trade = self.trade_service.get_trade_by_id(trade_id)
            assert individual_trade is not None
            assert individual_trade.id == trade_id
    
    @given(
        buy_quantity=st.integers(min_value=1, max_value=500),
        sell_quantity=st.integers(min_value=1, max_value=500),
    )
    def test_trade_execution_creates_records(self, buy_quantity, sell_quantity):
        """
        Verify that executing orders creates proper trade records
        """
        initial_trade_count = len(self.trade_service.get_all_trades())
        
        # Execute buy order
        buy_order = Order.create("TCS", OrderType.BUY, OrderStyle.MARKET, buy_quantity)
        buy_order.status = OrderStatus.PLACED
        self.storage.save_order(buy_order)
        
        buy_trade = self.trade_service.execute_market_order(buy_order)
        
        # Execute sell order
        sell_order = Order.create("INFY", OrderType.SELL, OrderStyle.MARKET, sell_quantity)
        sell_order.status = OrderStatus.PLACED
        self.storage.save_order(sell_order)
        
        sell_trade = self.trade_service.execute_market_order(sell_order)
        
        # Verify trade count increased
        final_trade_count = len(self.trade_service.get_all_trades())
        assert final_trade_count == initial_trade_count + 2
        
        # Verify trades are different
        assert buy_trade.id != sell_trade.id
        assert buy_trade.symbol != sell_trade.symbol
    
    @given(
        limit_price=st.decimals(min_value=Decimal('100'), max_value=Decimal('5000'), places=2),
        market_price=st.decimals(min_value=Decimal('100'), max_value=Decimal('5000'), places=2),
        quantity=st.integers(min_value=1, max_value=100),
    )
    def test_limit_order_execution_logic(self, limit_price, market_price, quantity):
        """
        Test limit order execution follows correct price logic
        """
        # Test BUY limit order
        buy_order = Order.create("TCS", OrderType.BUY, OrderStyle.LIMIT, quantity, limit_price)
        buy_order.status = OrderStatus.PLACED
        self.storage.save_order(buy_order)
        
        buy_trade = self.trade_service.execute_limit_order(buy_order, market_price)
        
        if market_price <= limit_price:
            # Should execute
            assert buy_trade is not None
            assert buy_trade.price == limit_price
        else:
            # Should not execute
            assert buy_trade is None
        
        # Test SELL limit order
        sell_order = Order.create("TCS", OrderType.SELL, OrderStyle.LIMIT, quantity, limit_price)
        sell_order.status = OrderStatus.PLACED
        self.storage.save_order(sell_order)
        
        sell_trade = self.trade_service.execute_limit_order(sell_order, market_price)
        
        if market_price >= limit_price:
            # Should execute
            assert sell_trade is not None
            assert sell_trade.price == limit_price
        else:
            # Should not execute
            assert sell_trade is None