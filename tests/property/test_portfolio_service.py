import pytest
from hypothesis import given, strategies as st
from decimal import Decimal
from app.services.portfolio_service import PortfolioService
from app.services.trade_service import TradeService
from app.models import Order, Trade, OrderType, OrderStyle, OrderStatus, PortfolioHolding
from app.storage import InMemoryStorage


class TestPortfolioServiceProperties:
    
    def setup_method(self):
        self.storage = InMemoryStorage()
        self.portfolio_service = PortfolioService()
        self.portfolio_service.storage = self.storage
        self.trade_service = TradeService()
        self.trade_service.storage = self.storage
    
    @given(
        quantity=st.integers(min_value=1, max_value=1000),
        average_price=st.decimals(min_value=Decimal('1'), max_value=Decimal('5000'), places=2),
        current_price=st.decimals(min_value=Decimal('1'), max_value=Decimal('5000'), places=2),
    )
    def test_portfolio_data_completeness(self, quantity, average_price, current_price):
        """
        Feature: trading-api-sdk, Property 10: Portfolio Data Completeness
        For any portfolio holding returned by the system, it should contain symbol, quantity, average_price, and current_value fields
        """
        # Create a holding
        holding = PortfolioHolding(
            symbol="TCS",
            quantity=quantity,
            average_price=average_price,
            current_value=quantity * current_price
        )
        self.storage.save_portfolio_holding(holding)
        
        # Get portfolio
        portfolio = self.portfolio_service.get_portfolio()
        
        assert len(portfolio) >= 1
        retrieved_holding = portfolio[0]
        
        # Verify all required fields are present
        assert hasattr(retrieved_holding, 'symbol')
        assert hasattr(retrieved_holding, 'quantity')
        assert hasattr(retrieved_holding, 'average_price')
        assert hasattr(retrieved_holding, 'current_value')
        
        # Verify field values are not None
        assert retrieved_holding.symbol is not None
        assert retrieved_holding.quantity is not None
        assert retrieved_holding.average_price is not None
        assert retrieved_holding.current_value is not None
        
        # Verify field types
        assert isinstance(retrieved_holding.symbol, str)
        assert isinstance(retrieved_holding.quantity, int)
        assert isinstance(retrieved_holding.average_price, Decimal)
        assert isinstance(retrieved_holding.current_value, Decimal)
    
    @given(
        quantity=st.integers(min_value=1, max_value=1000),
        market_price=st.decimals(min_value=Decimal('1'), max_value=Decimal('5000'), places=2),
    )
    def test_portfolio_calculation_accuracy(self, quantity, market_price):
        """
        Feature: trading-api-sdk, Property 11: Portfolio Calculation Accuracy
        For any portfolio holding, the current_value should equal quantity multiplied by current market price
        """
        # Update instrument price
        instrument = self.storage.get_instrument("TCS")
        if instrument:
            instrument.last_traded_price = market_price
            self.storage.save_instrument(instrument)
        
        # Create a holding
        holding = PortfolioHolding(
            symbol="TCS",
            quantity=quantity,
            average_price=Decimal('100'),  # Fixed average price
            current_value=Decimal('0')  # Will be recalculated
        )
        self.storage.save_portfolio_holding(holding)
        
        # Get updated portfolio (should recalculate current_value)
        portfolio = self.portfolio_service.get_portfolio()
        
        if portfolio:
            updated_holding = portfolio[0]
            expected_value = quantity * market_price
            assert updated_holding.current_value == expected_value
    
    @given(
        buy_quantity=st.integers(min_value=1, max_value=500),
        trade_price=st.decimals(min_value=Decimal('100'), max_value=Decimal('5000'), places=2),
    )
    def test_portfolio_trade_integration_buy(self, buy_quantity, trade_price):
        """
        Feature: trading-api-sdk, Property 12: Portfolio Trade Integration
        For any executed trade, the portfolio should reflect the position change immediately
        """
        # Get initial portfolio state
        initial_portfolio = self.portfolio_service.get_portfolio()
        initial_tcs_holding = None
        for holding in initial_portfolio:
            if holding.symbol == "TCS":
                initial_tcs_holding = holding
                break
        
        initial_quantity = initial_tcs_holding.quantity if initial_tcs_holding else 0
        
        # Create and execute a BUY trade
        order = Order.create("TCS", OrderType.BUY, OrderStyle.MARKET, buy_quantity)
        order.status = OrderStatus.PLACED
        self.storage.save_order(order)
        
        trade = Trade.create(order, trade_price)
        self.storage.save_trade(trade)
        
        # Update portfolio from trade
        self.portfolio_service.update_portfolio_from_trade(trade)
        
        # Verify portfolio reflects the change
        updated_portfolio = self.portfolio_service.get_portfolio()
        tcs_holding = None
        for holding in updated_portfolio:
            if holding.symbol == "TCS":
                tcs_holding = holding
                break
        
        assert tcs_holding is not None
        assert tcs_holding.quantity == initial_quantity + buy_quantity
    
    @given(
        sell_quantity=st.integers(min_value=1, max_value=100),
        trade_price=st.decimals(min_value=Decimal('100'), max_value=Decimal('5000'), places=2),
    )
    def test_portfolio_trade_integration_sell(self, sell_quantity, trade_price):
        """
        Feature: trading-api-sdk, Property 12: Portfolio Trade Integration
        For any executed trade, the portfolio should reflect the position change immediately
        """
        # Clear any existing TCS holdings first
        self.storage._portfolio.clear()
        
        # First ensure we have holdings to sell
        initial_holdings = 200  # Start with 200 shares
        self.storage.update_portfolio_position("TCS", initial_holdings, Decimal('3000'))
        
        # Verify initial state
        initial_holding = self.storage.get_portfolio_holding("TCS")
        assert initial_holding.quantity == initial_holdings
        
        # Create and execute a SELL trade
        order = Order.create("TCS", OrderType.SELL, OrderStyle.MARKET, sell_quantity)
        order.status = OrderStatus.PLACED
        self.storage.save_order(order)
        
        trade = Trade.create(order, trade_price)
        self.storage.save_trade(trade)
        
        # Update portfolio from trade
        self.portfolio_service.update_portfolio_from_trade(trade)
        
        # Verify portfolio reflects the change
        updated_portfolio = self.portfolio_service.get_portfolio()
        tcs_holding = None
        for holding in updated_portfolio:
            if holding.symbol == "TCS":
                tcs_holding = holding
                break
        
        expected_quantity = initial_holdings - sell_quantity
        if expected_quantity > 0:
            assert tcs_holding is not None
            assert tcs_holding.quantity == expected_quantity
        else:
            # If we sold all shares, holding should be removed or have 0 quantity
            assert tcs_holding is None or tcs_holding.quantity == 0
    
    def test_portfolio_value_calculation_consistency(self):
        """
        Test that portfolio value calculations are consistent
        """
        # Create multiple holdings
        holdings_data = [
            ("TCS", 100, Decimal('3000'), Decimal('3450.25')),
            ("INFY", 50, Decimal('1400'), Decimal('1520.40')),
            ("RELIANCE", 25, Decimal('2700'), Decimal('2850.10')),
        ]
        
        expected_total = Decimal('0')
        for symbol, quantity, avg_price, current_price in holdings_data:
            # Update instrument price
            instrument = self.storage.get_instrument(symbol)
            if instrument:
                instrument.last_traded_price = current_price
                self.storage.save_instrument(instrument)
            
            # Create holding
            holding = PortfolioHolding(
                symbol=symbol,
                quantity=quantity,
                average_price=avg_price,
                current_value=quantity * current_price
            )
            self.storage.save_portfolio_holding(holding)
            expected_total += quantity * current_price
        
        # Calculate portfolio value
        calculated_total = self.portfolio_service.calculate_portfolio_value()
        
        assert calculated_total == expected_total