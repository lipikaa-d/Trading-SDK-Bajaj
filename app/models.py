from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
import uuid


class OrderType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderStyle(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderStatus(str, Enum):
    NEW = "NEW"
    PLACED = "PLACED"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"


class InstrumentType(str, Enum):
    STOCK = "STOCK"
    BOND = "BOND"
    ETF = "ETF"
    OPTION = "OPTION"


@dataclass
class Instrument:
    symbol: str
    exchange: str
    instrument_type: InstrumentType
    last_traded_price: Decimal


@dataclass
class Order:
    id: str
    symbol: str
    order_type: OrderType
    order_style: OrderStyle
    quantity: int
    price: Optional[Decimal]
    status: OrderStatus
    created_at: datetime

    @classmethod
    def create(cls, symbol: str, order_type: OrderType, order_style: OrderStyle, 
               quantity: int, price: Optional[Decimal] = None) -> 'Order':
        return cls(
            id=str(uuid.uuid4()),
            symbol=symbol,
            order_type=order_type,
            order_style=order_style,
            quantity=quantity,
            price=price,
            status=OrderStatus.NEW,
            created_at=datetime.now()
        )


@dataclass
class Trade:
    id: str
    order_id: str
    symbol: str
    quantity: int
    price: Decimal
    executed_at: datetime

    @classmethod
    def create(cls, order: Order, execution_price: Decimal) -> 'Trade':
        return cls(
            id=str(uuid.uuid4()),
            order_id=order.id,
            symbol=order.symbol,
            quantity=order.quantity,
            price=execution_price,
            executed_at=datetime.now()
        )


@dataclass
class PortfolioHolding:
    symbol: str
    quantity: int
    average_price: Decimal
    current_value: Decimal

    def update_position(self, trade_quantity: int, trade_price: Decimal, current_market_price: Decimal):
        if self.quantity + trade_quantity == 0:
            self.quantity = 0
            self.average_price = Decimal('0')
            self.current_value = Decimal('0')
            return

        total_cost = (self.quantity * self.average_price) + (trade_quantity * trade_price)
        self.quantity += trade_quantity
        self.average_price = total_cost / self.quantity if self.quantity != 0 else Decimal('0')
        self.current_value = self.quantity * current_market_price