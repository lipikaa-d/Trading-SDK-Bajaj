import threading
from typing import Dict, List, Optional
from decimal import Decimal
from app.models import Instrument, Order, Trade, PortfolioHolding, InstrumentType


class InMemoryStorage:
    def __init__(self):
        self._lock = threading.RLock()
        self._instruments: Dict[str, Instrument] = {}
        self._orders: Dict[str, Order] = {}
        self._trades: Dict[str, Trade] = {}
        self._portfolio: Dict[str, PortfolioHolding] = {}
        self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        sample_instruments = [
            Instrument("TCS", "NSE", InstrumentType.STOCK, Decimal("3450.25")),
            Instrument("INFY", "NSE", InstrumentType.STOCK, Decimal("1520.40")),
            Instrument("RELIANCE", "NSE", InstrumentType.STOCK, Decimal("2850.10")),
            Instrument("HDFC", "NSE", InstrumentType.STOCK, Decimal("1680.75")),
            Instrument("ICICIBANK", "NSE", InstrumentType.STOCK, Decimal("950.30")),
        ]
        
        with self._lock:
            for instrument in sample_instruments:
                self._instruments[instrument.symbol] = instrument
    
    def save_instrument(self, instrument: Instrument) -> None:
        with self._lock:
            self._instruments[instrument.symbol] = instrument
    
    def get_instrument(self, symbol: str) -> Optional[Instrument]:
        with self._lock:
            return self._instruments.get(symbol)
    
    def get_all_instruments(self) -> List[Instrument]:
        with self._lock:
            return list(self._instruments.values())
    
    def save_order(self, order: Order) -> None:
        with self._lock:
            self._orders[order.id] = order
    
    def get_order(self, order_id: str) -> Optional[Order]:
        with self._lock:
            return self._orders.get(order_id)
    
    def get_all_orders(self) -> List[Order]:
        with self._lock:
            return list(self._orders.values())
    
    def update_order_status(self, order_id: str, status) -> bool:
        with self._lock:
            if order_id in self._orders:
                self._orders[order_id].status = status
                return True
            return False
    
    def save_trade(self, trade: Trade) -> None:
        with self._lock:
            self._trades[trade.id] = trade
    
    def get_trade(self, trade_id: str) -> Optional[Trade]:
        with self._lock:
            return self._trades.get(trade_id)
    
    def get_all_trades(self) -> List[Trade]:
        with self._lock:
            return list(self._trades.values())
    
    def save_portfolio_holding(self, holding: PortfolioHolding) -> None:
        with self._lock:
            self._portfolio[holding.symbol] = holding
    
    def get_portfolio_holding(self, symbol: str) -> Optional[PortfolioHolding]:
        with self._lock:
            return self._portfolio.get(symbol)
    
    def get_all_portfolio_holdings(self) -> List[PortfolioHolding]:
        with self._lock:
            return list(self._portfolio.values())
    
    def get_portfolio_holdings(self) -> List[PortfolioHolding]:
        """Alias for get_all_portfolio_holdings for compatibility"""
        return self.get_all_portfolio_holdings()
    
    def get_current_timestamp(self) -> str:
        """Get current timestamp as ISO string"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def update_portfolio_position(self, symbol: str, quantity_change: int, trade_price: Decimal) -> None:
        with self._lock:
            current_market_price = self._instruments.get(symbol).last_traded_price if symbol in self._instruments else trade_price
            
            if symbol in self._portfolio:
                holding = self._portfolio[symbol]
                holding.update_position(quantity_change, trade_price, current_market_price)
                if holding.quantity == 0:
                    del self._portfolio[symbol]
            else:
                if quantity_change > 0:
                    self._portfolio[symbol] = PortfolioHolding(
                        symbol=symbol,
                        quantity=quantity_change,
                        average_price=trade_price,
                        current_value=quantity_change * current_market_price
                    )


storage = InMemoryStorage()
