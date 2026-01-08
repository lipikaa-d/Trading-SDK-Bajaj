from fastapi import HTTPException
from pydantic import ValidationError


class TradingAPIException(Exception):
    """Base exception for trading API"""
    def __init__(self, message: str, error_code: str = "TRADING_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class InstrumentNotFoundError(TradingAPIException):
    def __init__(self, symbol: str):
        super().__init__(f"Instrument {symbol} not found", "INSTRUMENT_NOT_FOUND")


class OrderNotFoundError(TradingAPIException):
    def __init__(self, order_id: str):
        super().__init__(f"Order with ID {order_id} not found", "ORDER_NOT_FOUND")


class OrderValidationError(TradingAPIException):
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR")


class InsufficientBalanceError(TradingAPIException):
    def __init__(self, symbol: str, required: int, available: int):
        super().__init__(
            f"Insufficient balance for {symbol}: required {required}, available {available}",
            "INSUFFICIENT_BALANCE"
        )


class InvalidOrderStateError(TradingAPIException):
    def __init__(self, order_id: str, current_state: str, required_state: str):
        super().__init__(
            f"Order {order_id} is in {current_state} state, required {required_state}",
            "INVALID_ORDER_STATE"
        )


def create_error_response(error_code: str, message: str, details: dict = None):
    """Create standardized error response"""
    error_response = {
        "error": {
            "code": error_code,
            "message": message
        }
    }
    
    if details:
        error_response["error"]["details"] = details
    
    return error_response


def get_http_status_for_error(error_code: str) -> int:
    """Map error codes to HTTP status codes"""
    status_map = {
        "INSTRUMENT_NOT_FOUND": 404,
        "ORDER_NOT_FOUND": 404,
        "VALIDATION_ERROR": 400,
        "INSUFFICIENT_BALANCE": 422,
        "INVALID_ORDER_STATE": 422,
        "INTERNAL_SERVER_ERROR": 500,
    }
    
    return status_map.get(error_code, 500)