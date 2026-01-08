import pytest
from decimal import Decimal
from app.services.portfolio_service import PortfolioService
from app.models import Order, Trade, OrderType, OrderStyle, OrderStatus, PortfolioHolding
from app.storage import InMemoryStorage


class TestPortfolioService:
    
    def setup_method(self):
        self.storage = InMemoryStorage()
        self.portfolio_service = PortfolioService()
        self.portfolio_service.storage = self.storage
    
    def test_get_empty_portfolio(self):
        portfolio = self.portfolio_service.get_portfolio()
        assert isinstance(portfolio, list)
        assert len(portfolio) == 0
    
    def test_get_portfolio_with_holdings(self):
        # Create some holdings
        holding1 = PortfolioHolding("TCS", 100, Decimal("3400.00"), Decimal("345000.00"))
        holding2 = PortfolioHolding("INFY", 50, Decimal("1500.00"), Decimal("76020.00"))
        
        self.storage.save_portfolio_holding(holding1)
        self.storage.save_portfolio_holding(holding2)
        
        portfolio = self.portfolio_service.get_portfolio()
        
        assert len(portfolio) == 2
        symbols = [holding.symbol for holding in portfolio]
        assert "TCS" in symbols
        assert "INFY" in symbols
    
    def test_get_holding_existing(self):
        holding = PortfolioHolding("TCS", 100, Decimal("3400.00"), Decimal("345000.00"))
        self.storage.save_portfolio_holding(holding)
        
        retrieved = self.portfolio_service.get_holding("TCS")
        
        assert retrieved is not None
        assert retrieved.symbol == "TCS"
        assert retrieved.quantity == 100
        assert retrieved.average_price == Decimal("3400.00")
    
    def test_get_holding_nonexistent(self):
        result = self.portfolio_service.get_holding("NONEXISTENT")
        assert result is None
    
    def test_update_portfolio_from_buy_trade(self):
        # Create and save order
        order = Order.create("TCS", OrderType.BUY, OrderStyle.MARKET, 100)
        order.status = OrderStatus.EXECUTED
        self.storage.save_order(order)
        
        # Create trade
        trade = Trade.create(order, Decimal("3450.25"))
        self.storage.save_trade(trade)
        
        # Update portfolio
        self.portfolio_service.update_portfolio_from_trade(trade)
        
        # Verify portfolio updated
        holding = self.storage.get_portfolio_holding("TCS")
        assert holding is not None
        assert holding.quantity == 100
        assert holding.average_price == Decimal("3450.25")
    
    def test_update_portfolio_from_sell_trade(self):
        # First create initial holding
        self.storage.update_portfolio_position("TCS", 200, Decimal("3400.00"))
        
        # Create sell order and trade
        order = Order.create("TCS", OrderType.SELL, OrderStyle.MARKET, 50)
        order.status = OrderStatus.EXECUTED
        self.storage.save_order(order)
        
        trade = Trade.create(order, Decimal("3500.00"))
        self.storage.save_trade(trade)
        
        # Update portfolio
        self.portfolio_service.update_portfolio_from_trade(trade)
        
        # Verify portfolio updated
        holding = self.storage.get_portfolio_holding("TCS")
        assert holding is not None
        assert holding.quantity == 150  # 200 - 50
    
    def test_calculate_portfolio_value(self):
        # Create holdings with known values
        holding1 = PortfolioHolding("TCS", 100, Decimal("3400.00"), Decimal("345025.00"))
        holding2 = PortfolioHolding("INFY", 50, Decimal("1500.00"), Decimal("76020.00"))
        
        self.storage.save_portfolio_holding(holding1)
        self.storage.save_portfolio_holding(holding2)
        
        total_value = self.portfolio_service.calculate_portfolio_value()
        expected_value = Decimal("345025.00") + Decimal("76020.00")
        
        assert total_value == expected_value
    
    def test_calculate_portfolio_value_empty(self):
        total_value = self.portfolio_service.calculate_portfolio_value()
        assert total_value == Decimal("0")
    
    def test_calculate_portfolio_pnl_profit(self):
        # Create holding with profit (current > cost basis)
        # Note: get_portfolio() will update current_value with market price
        holding = PortfolioHolding(
            symbol="TCS",
            quantity=100,
            average_price=Decimal("3400.00"),  # Cost basis: 340,000
            current_value=Decimal("350000.00")  # Will be updated to market price
        )
        self.storage.save_portfolio_holding(holding)
        
        pnl = self.portfolio_service.calculate_portfolio_pnl()
        
        # PnL should be based on market price (3450.25) vs average price (3400.00)
        market_price = Decimal("3450.25")  # TCS market price from sample data
        expected_pnl = (100 * market_price) - (100 * Decimal("3400.00"))
        
        assert pnl == expected_pnl
        assert pnl > 0  # Should be profit
    
    def test_calculate_portfolio_pnl_loss(self):
        # Create holding with loss (current < cost basis)
        holding = PortfolioHolding(
            symbol="TCS",
            quantity=100,
            average_price=Decimal("3500.00"),  # Cost basis: 350,000
            current_value=Decimal("340000.00")  # Will be updated to market price
        )
        self.storage.save_portfolio_holding(holding)
        
        pnl = self.portfolio_service.calculate_portfolio_pnl()
        
        # PnL should be based on market price (3450.25) vs average price (3500.00)
        market_price = Decimal("3450.25")  # TCS market price from sample data
        expected_pnl = (100 * market_price) - (100 * Decimal("3500.00"))
        
        assert pnl == expected_pnl
        assert pnl < 0  # Should be loss
    
    def test_calculate_portfolio_pnl_empty(self):
        pnl = self.portfolio_service.calculate_portfolio_pnl()
        assert pnl == Decimal("0")
    
    def test_get_portfolio_summary(self):
        # Create some holdings
        holding1 = PortfolioHolding("TCS", 100, Decimal("3400.00"), Decimal("345000.00"))
        holding2 = PortfolioHolding("INFY", 50, Decimal("1500.00"), Decimal("76000.00"))
        
        self.storage.save_portfolio_holding(holding1)
        self.storage.save_portfolio_holding(holding2)
        
        summary = self.portfolio_service.get_portfolio_summary()
        
        assert "holdings" in summary
        assert "total_value" in summary
        assert "total_pnl" in summary
        assert "holdings_count" in summary
        
        assert len(summary["holdings"]) == 2
        assert summary["holdings_count"] == 2
        assert summary["total_value"] > 0
        assert isinstance(summary["total_pnl"], Decimal)
    
    def test_portfolio_current_value_updates_with_market_price(self):
        # Create holding
        holding = PortfolioHolding("TCS", 100, Decimal("3400.00"), Decimal("340000.00"))
        self.storage.save_portfolio_holding(holding)
        
        # Get portfolio (should update current_value with market price)
        portfolio = self.portfolio_service.get_portfolio()
        
        assert len(portfolio) == 1
        updated_holding = portfolio[0]
        
        # Should be updated to current market price (3450.25 from sample data)
        expected_value = 100 * Decimal("3450.25")
        assert updated_holding.current_value == expected_value
    
    def test_mathematical_accuracy_of_calculations(self):
        # Test with precise decimal calculations
        quantity = 123
        average_price = Decimal("1234.56")
        current_price = Decimal("1345.67")
        
        # Update instrument price
        instrument = self.storage.get_instrument("TCS")
        if instrument:
            instrument.last_traded_price = current_price
            self.storage.save_instrument(instrument)
        
        # Create holding
        holding = PortfolioHolding("TCS", quantity, average_price, Decimal("0"))
        self.storage.save_portfolio_holding(holding)
        
        # Get updated portfolio
        portfolio = self.portfolio_service.get_portfolio()
        updated_holding = portfolio[0]
        
        # Verify mathematical accuracy
        expected_current_value = quantity * current_price
        expected_cost_basis = quantity * average_price
        expected_pnl = expected_current_value - expected_cost_basis
        
        assert updated_holding.current_value == expected_current_value
        
        calculated_pnl = self.portfolio_service.calculate_portfolio_pnl()
        assert calculated_pnl == expected_pnl