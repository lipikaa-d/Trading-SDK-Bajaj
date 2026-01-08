from typing import List, Optional
from decimal import Decimal
from app.models import Trade, Order, OrderStatus, OrderStyle
from app.storage import storage


class TradeService:
    def __init__(self):
        self.storage = storage
    
    def execute_market_order(self, order: Order) -> Trade:
        """Execute a market order immediately at current market price"""
        if order.order_style != OrderStyle.MARKET:
            raise ValueError("Only market orders can be executed immediately")
        
        # Get current market price from instrument
        instrument = self.storage.get_instrument(order.symbol)
        if not instrument:
            raise ValueError(f"Instrument {order.symbol} not found")
        
        execution_price = instrument.last_traded_price
        
        # Create trade record
        trade = Trade.create(order, execution_price)
        
        # Save trade
        self.storage.save_trade(trade)
        
        # Update order status to EXECUTED
        self.storage.update_order_status(order.id, OrderStatus.EXECUTED)
        
        # Update portfolio position
        quantity_change = order.quantity if order.order_type.value == "BUY" else -order.quantity
        self.storage.update_portfolio_position(order.symbol, quantity_change, execution_price)
        
        return trade
    
    def execute_limit_order(self, order: Order, market_price: Decimal) -> Optional[Trade]:
        """Execute a limit order if price conditions are met"""
        if order.order_style != OrderStyle.LIMIT or order.price is None:
            raise ValueError("Order must be a limit order with price")
        
        # Check if limit order can be executed
        can_execute = False
        if order.order_type.value == "BUY" and market_price <= order.price:
            can_execute = True
        elif order.order_type.value == "SELL" and market_price >= order.price:
            can_execute = True
        
        if not can_execute:
            return None
        
        # Execute at limit price
        trade = Trade.create(order, order.price)
        
        # Save trade
        self.storage.save_trade(trade)
        
        # Update order status to EXECUTED
        self.storage.update_order_status(order.id, OrderStatus.EXECUTED)
        
        # Update portfolio position
        quantity_change = order.quantity if order.order_type.value == "BUY" else -order.quantity
        self.storage.update_portfolio_position(order.symbol, quantity_change, order.price)
        
        return trade
    
    def get_all_trades(self) -> List[Trade]:
        """Get all executed trades"""
        return self.storage.get_all_trades()
    
    def get_trade_by_id(self, trade_id: str) -> Optional[Trade]:
        """Get a specific trade by ID"""
        return self.storage.get_trade(trade_id)
    
    def get_trades_for_symbol(self, symbol: str) -> List[Trade]:
        """Get all trades for a specific symbol"""
        all_trades = self.storage.get_all_trades()
        return [trade for trade in all_trades if trade.symbol == symbol]
    
    def simulate_market_execution(self) -> List[Trade]:
        """Simulate execution of all pending market orders"""
        executed_trades = []
        
        # Get all orders with PLACED status
        all_orders = self.storage.get_all_orders()
        market_orders = [order for order in all_orders 
                        if order.status == OrderStatus.PLACED and order.order_style == OrderStyle.MARKET]
        
        # Execute all market orders
        for order in market_orders:
            try:
                trade = self.execute_market_order(order)
                executed_trades.append(trade)
            except Exception as e:
                # Log error but continue with other orders
                print(f"Failed to execute order {order.id}: {e}")
        
        return executed_trades


trade_service = TradeService()