# Trading API SDK

A comprehensive FastAPI-based trading system that simulates core trading workflows including instrument management, order placement, trade execution, and portfolio tracking.

## Features

- **Instrument Management**: View available financial instruments
- **Order Management**: Place BUY/SELL orders with MARKET/LIMIT styles
- **Trade Execution**: Automatic execution of market orders
- **Portfolio Tracking**: Real-time portfolio holdings and calculations
- **Comprehensive Error Handling**: Proper HTTP status codes and descriptive error messages
- **Property-Based Testing**: Extensive test coverage with Hypothesis

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Run the API

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Instruments
- `GET /api/v1/instruments` - List all available instruments

### Orders
- `POST /api/v1/orders` - Place a new order
- `GET /api/v1/orders/{order_id}` - Get order status

### Trades
- `GET /api/v1/trades` - List all executed trades

### Portfolio
- `GET /api/v1/portfolio` - Get current portfolio holdings

### System
- `GET /health` - Health check with system statistics

## Usage Examples

### Place a Market Order

```bash
curl -X POST "http://localhost:8000/api/v1/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "TCS",
    "quantity": 10,
    "order_type": "BUY",
    "order_style": "MARKET"
  }'
```

### Place a Limit Order

```bash
curl -X POST "http://localhost:8000/api/v1/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "INFY",
    "quantity": 5,
    "order_type": "SELL",
    "order_style": "LIMIT",
    "price": 1500.00
  }'
```

### Check Portfolio

```bash
curl "http://localhost:8000/api/v1/portfolio"
```

## Testing

Run all tests:
```bash
pytest
```

Run specific test categories:
```bash
# Integration tests
pytest tests/integration/

# Property-based tests
pytest tests/property/

# Unit tests
pytest tests/unit/
```

## Architecture

- **FastAPI**: Modern web framework with automatic API documentation
- **Pydantic**: Data validation and serialization
- **In-Memory Storage**: Thread-safe storage for development/testing
- **Modular Services**: Separate services for orders, trades, portfolio, and instruments
- **Comprehensive Error Handling**: Custom exceptions with proper HTTP status codes

## Sample Data

The system comes pre-loaded with 5 sample instruments:
- TCS (₹3,450.25)
- INFY (₹1,520.40)
- RELIANCE (₹2,850.10)
- HDFC (₹1,680.75)
- ICICIBANK (₹950.30)

## System Status

 **All Core Requirements Implemented**
- 121+ tests passing (property-based + unit + integration)
- Complete trading workflow functional
- Comprehensive error handling
- Real-time portfolio calculations
- API documentation available

## Assumptions Made
**Following Assumptions were made** 
- Orders are executed immediately (simulation).
- Each executed order results in exactly one trade.
- Portfolio is computed dynamically from executed trades.
- The system supports a single user (mock authentication).
- All data is stored in memory and is reset when the server restarts.