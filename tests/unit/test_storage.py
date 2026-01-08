import pytest
import threading
import time
from decimal import Decimal
from app.storage import InMemoryStorage
from app.models import Instrument, Order, Trade, PortfolioHolding, InstrumentType, OrderType, OrderStyle, OrderStatus


class TestInMemoryStorage:
    
    def setup_method(self):
        self.storage = InMemoryStorage()
    
    def test_initialize_with_sample_instruments(self):
        instruments = self.storage.get_all_instruments()
        assert len(instruments) == 5
        symbols = [inst.symbol for inst in instruments]
        assert "TCS" in symbols
        assert "INFY" in symbols
        assert "RELIANCE" in symbols
    
    def test_save_and_get_instrument(self):
        instrument = Instrument("AAPL", "NASDAQ", InstrumentType.STOCK, Decimal("150.25"))
        self.storage.save_instrument(instrument)
        
        retrieved = self.storage.get_instrument("AAPL")
        assert retrieved is not None
        assert retrieved.symbol == "AAPL"
        assert retrieved.exchange == "NASDAQ"
        assert retrieved.last_traded_price == Decimal("150.25")
    
    def test_save_and_get_order(self):
        order = Order.create("TCS", OrderType.BUY, OrderStyle.MARKET, 100)
        self.storage.save_order(order)
        
        retrieved = self.storage.get_order(order.id)
        assert retrieved is not None
        assert retrieved.symbol == "TCS"
        assert retrieved.quantity == 100
        assert retrieved.status == OrderStatus.NEW
    
    def test_update_order_status(self):
        order = Order.create("TCS", OrderType.BUY, OrderStyle.MARKET, 100)
        self.storage.save_order(order)
        
        success = self.storage.update_order_status(order.id, OrderStatus.EXECUTED)
        assert success is True
        
        retrieved = self.storage.get_order(order.id)
        assert retrieved.status == OrderStatus.EXECUTED
    
    def test_save_and_get_trade(self):
        order = Order.create("TCS", OrderType.BUY, OrderStyle.MARKET, 100)
        trade = Trade.create(order, Decimal("3450.25"))
        self.storage.save_trade(trade)
        
        retrieved = self.storage.get_trade(trade.id)
        assert retrieved is not None
        assert retrieved.symbol == "TCS"
        assert retrieved.quantity == 100
        assert retrieved.price == Decimal("3450.25")
    
    def test_portfolio_operations(self):
        holding = PortfolioHolding("TCS", 100, Decimal("3400.00"), Decimal("345000.00"))
        self.storage.save_portfolio_holding(holding)
        
        retrieved = self.storage.get_portfolio_holding("TCS")
        assert retrieved is not None
        assert retrieved.quantity == 100
        assert retrieved.average_price == Decimal("3400.00")
    
    def test_update_portfolio_position_new_holding(self):
        self.storage.update_portfolio_position("TCS", 100, Decimal("3450.25"))
        
        holding = self.storage.get_portfolio_holding("TCS")
        assert holding is not None
        assert holding.quantity == 100
        assert holding.average_price == Decimal("3450.25")
    
    def test_update_portfolio_position_existing_holding(self):
        initial_holding = PortfolioHolding("TCS", 100, Decimal("3400.00"), Decimal("345000.00"))
        self.storage.save_portfolio_holding(initial_holding)
        
        self.storage.update_portfolio_position("TCS", 50, Decimal("3500.00"))
        
        updated_holding = self.storage.get_portfolio_holding("TCS")
        assert updated_holding.quantity == 150
    
    def test_thread_safety_concurrent_operations(self):
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                for i in range(10):
                    order = Order.create(f"STOCK{worker_id}", OrderType.BUY, OrderStyle.MARKET, i + 1)
                    self.storage.save_order(order)
                    retrieved = self.storage.get_order(order.id)
                    results.append(retrieved.id)
                    time.sleep(0.001)
            except Exception as e:
                errors.append(str(e))
        
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        assert len(errors) == 0
        assert len(results) == 50
        assert len(set(results)) == 50  # All IDs should be unique