from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from app.models import OrderType, OrderStyle, OrderStatus, InstrumentType


class OrderRequest(BaseModel):
    symbol: str
    order_type: OrderType
    order_style: OrderStyle
    quantity: int = Field(gt=0)
    price: Optional[Decimal] = None

    def validate_limit_order(self):
        if self.order_style == OrderStyle.LIMIT and self.price is None:
            raise ValueError("Price is required for limit orders")


class OrderResponse(BaseModel):
    id: str
    symbol: str
    order_type: OrderType
    order_style: OrderStyle
    quantity: int
    price: Optional[Decimal]
    status: OrderStatus
    created_at: datetime


class InstrumentResponse(BaseModel):
    symbol: str
    exchange: str
    instrument_type: InstrumentType
    last_traded_price: Decimal


class TradeResponse(BaseModel):
    id: str
    order_id: str
    symbol: str
    quantity: int
    price: Decimal
    executed_at: datetime


class PortfolioResponse(BaseModel):
    symbol: str
    quantity: int
    average_price: Decimal
    current_value: Decimal


class ErrorResponse(BaseModel):
    error: dict


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[dict] = None
