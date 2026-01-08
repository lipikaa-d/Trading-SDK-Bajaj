from typing import List, Optional
from decimal import Decimal
from app.models import PortfolioHolding, Trade, OrderType
from app.storage import storage


class PortfolioService:
    def __init__(self):
        self.storage = storage
    
    def get_portfolio(self) -> List[PortfolioHolding]:
        """Get all current portfolio holdings"""
        holdings = self.storage.get_all_portfolio_holdings()
        
        # Update current values based on latest market prices
        updated_holdings = []
        for holding in holdings:
            instrument = self.storage.get_instrument(holding.symbol)
            if instrument:
                # Recalculate current value with latest market price
                current_market_price = instrument.last_traded_price
                updated_holding = PortfolioHolding(
                    symbol=holding.symbol,
                    quantity=holding.quantity,
                    average_price=holding.average_price,
                    current_value=holding.quantity * current_market_price
                )
                updated_holdings.append(updated_holding)
                
                # Update storage with new current value
                self.storage.save_portfolio_holding(updated_holding)
        
        return updated_holdings
    
    def get_holding(self, symbol: str) -> Optional[PortfolioHolding]:
        """Get holding for a specific symbol"""
        holding = self.storage.get_portfolio_holding(symbol)
        if not holding:
            return None
        
        # Update current value with latest market price
        instrument = self.storage.get_instrument(symbol)
        if instrument:
            current_market_price = instrument.last_traded_price
            updated_holding = PortfolioHolding(
                symbol=holding.symbol,
                quantity=holding.quantity,
                average_price=holding.average_price,
                current_value=holding.quantity * current_market_price
            )
            
            # Update storage
            self.storage.save_portfolio_holding(updated_holding)
            return updated_holding
        
        return holding
    
    def update_portfolio_from_trade(self, trade: Trade):
        """Update portfolio based on executed trade"""
        # Determine quantity change based on trade type
        # Note: We need to get the original order to determine BUY/SELL
        order = self.storage.get_order(trade.order_id)
        if not order:
            raise ValueError(f"Order {trade.order_id} not found")
        
        quantity_change = trade.quantity if order.order_type == OrderType.BUY else -trade.quantity
        
        # Update portfolio position
        self.storage.update_portfolio_position(trade.symbol, quantity_change, trade.price)
    
    def calculate_portfolio_value(self) -> Decimal:
        """Calculate total portfolio value"""
        holdings = self.get_portfolio()
        total_value = Decimal('0')
        
        for holding in holdings:
            total_value += holding.current_value
        
        return total_value
    
    def calculate_portfolio_pnl(self) -> Decimal:
        """Calculate total portfolio profit/loss"""
        holdings = self.get_portfolio()
        total_pnl = Decimal('0')
        
        for holding in holdings:
            cost_basis = holding.quantity * holding.average_price
            current_value = holding.current_value
            pnl = current_value - cost_basis
            total_pnl += pnl
        
        return total_pnl
    
    def get_portfolio_summary(self) -> dict:
        """Get portfolio summary with totals"""
        holdings = self.get_portfolio()
        total_value = self.calculate_portfolio_value()
        total_pnl = self.calculate_portfolio_pnl()
        
        return {
            "holdings": holdings,
            "total_value": total_value,
            "total_pnl": total_pnl,
            "holdings_count": len(holdings)
        }


portfolio_service = PortfolioService()