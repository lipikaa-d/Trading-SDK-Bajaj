# Trading API SDK - Complete Code Architecture Documentation

## Overview
This document provides a comprehensive explanation of every file and component in the Trading API SDK codebase. The system is built using FastAPI and follows a clean architecture pattern with clear separation of concerns.

## Project Structure
```
trading-api-sdk/
├── app/                    # Main application code
│   ├── main.py            # FastAPI application setup
│   ├── models.py          # Domain models and enums
│   ├── schemas.py         # Pydantic request/response schemas
│   ├── storage.py         # In-memory data storage
│   ├── exceptions.py      # Custom exception classes
│   ├── routes/            # API endpoint definitions
│   │   ├── __init__.py
│   │   ├── instruments.py
│   │   ├── orders.py
│   │   ├── trades.py
│   │   └── portfolio.py
│   ├── services/          # Business logic services
│   │   ├── __init__.py
│   │   ├── instrument_service.py
│   │   ├── order_service.py
│   │   ├── trade_service.py
│   │   └── portfolio_service.py
│   └── utils/             # Utility functions
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── property/         # Property-based tests
├── requirements.txt       # Python dependencies
└── README.md             # Project documentation
```

## Core Application Files

### 1. app/main.py - FastAPI Application Setup
**Purpose**: Main application entry point with FastAPI configuration, middleware, and exception handlers.

**Key Components**:
- **FastAPI App Configuration**: Sets up the main application with title, description, and version
- **CORS Middleware**: Enables cross-origin requests for web clients
- **Logging Configuration**: Structured logging with file and console output
- **Exception Handlers**: Global error handling for different exception types
- **Startup/Shutdown Events**: Application lifecycle management
- **Health Check Endpoint**: System status monitoring
- **Router Registration**: Includes all API route modules

**Critical Features**:
```python
# Custom exception handling
@app.exception_handler(TradingAPIException)
async def trading_api_exception_handler(request: Request, exc: TradingAPIException):
    # Returns structured error responses with proper HTTP status codes

# Comprehensive health check
@app.get("/health")
async def health_check():
    # Returns system statistics and component status
```

### 2. app/models.py - Domain Models
**Purpose**: Core business entities and enums that represent the trading domain.

**Models Defined**:
- **Enums**: OrderType (BUY/SELL), OrderStyle (MARKET/LIMIT), OrderStatus (NEW/PLACED/EXECUTED/CANCELLED), InstrumentType (STOCK/BOND/ETF/OPTION)
- **Instrument**: Financial instrument with symbol, exchange, type, and price
- **Order**: Trading order with all necessary fields and factory method
- **Trade**: Executed trade record with order reference
- **PortfolioHolding**: Portfolio position with quantity, average price, and current value

**Key Features**:
```python
@dataclass
class Order:
    # Factory method for creating new orders
    @classmethod
    def create(cls, symbol: str, order_type: OrderType, ...):
        return cls(id=str(uuid.uuid4()), ...)

@dataclass
class PortfolioHolding:
    # Method to update position when trades execute
    def update_position(self, trade_quantity: int, trade_price: Decimal, ...):
        # Calculates new average price and current value
```

### 3. app/schemas.py - Pydantic Schemas
**Purpose**: Request/response validation and serialization using Pydantic.

**Schemas Defined**:
- **OrderRequest**: Validates incoming order placement requests
- **OrderResponse**: Standardizes order data in API responses
- **InstrumentResponse**: Formats instrument data for API responses
- **TradeResponse**: Formats trade data for API responses
- **PortfolioResponse**: Formats portfolio holdings for API responses
- **ErrorResponse**: Standardizes error response format

**Validation Features**:
```python
class OrderRequest(BaseModel):
    quantity: int = Field(gt=0)  # Ensures positive quantity
    
    def validate_limit_order(self):
        # Custom validation for limit orders requiring price
```

### 4. app/storage.py - In-Memory Storage
**Purpose**: Thread-safe in-memory data storage with sample data initialization.

**Key Features**:
- **Thread Safety**: Uses RLock for concurrent access protection
- **Sample Data**: Pre-loads 5 Indian stock instruments
- **CRUD Operations**: Complete create, read, update, delete operations for all entities
- **Portfolio Management**: Handles position updates when trades execute

**Storage Methods**:
```python
class InMemoryStorage:
    def __init__(self):
        self._lock = threading.RLock()  # Thread safety
        self._instruments: Dict[str, Instrument] = {}
        self._orders: Dict[str, Order] = {}
        self._trades: Dict[str, Trade] = {}
        self._portfolio: Dict[str, PortfolioHolding] = {}
    
    def update_portfolio_position(self, symbol: str, quantity_change: int, trade_price: Decimal):
        # Complex logic for updating portfolio positions
```

### 5. app/exceptions.py - Custom Exceptions
**Purpose**: Custom exception classes with proper HTTP status code mapping.

**Exception Classes**:
- **TradingAPIException**: Base exception class
- **OrderValidationError**: Order validation failures
- **InstrumentNotFoundError**: Invalid instrument symbols
- **OrderNotFoundError**: Invalid order IDs
- **TradeExecutionError**: Trade execution failures

**Error Response Creation**:
```python
def create_error_response(error_code: str, message: str, details: dict = None):
    # Creates standardized error response format
    
def get_http_status_for_error(error_code: str) -> int:
    # Maps error codes to appropriate HTTP status codes
```

## Service Layer

### 1. app/services/order_service.py - Order Management
**Purpose**: Business logic for order placement, validation, and status management.

**Key Responsibilities**:
- **Order Validation**: Validates all order parameters before placement
- **Order Placement**: Creates and stores new orders
- **Market Order Execution**: Automatically executes market orders
- **Status Management**: Tracks order state transitions

**Critical Logic**:
```python
def place_order(self, order_request: OrderRequest) -> Order:
    self._validate_order_request(order_request)  # Comprehensive validation
    order = Order.create(...)  # Create order
    order.status = OrderStatus.PLACED
    self.storage.save_order(order)
    
    # Auto-execute market orders
    if order.order_style == OrderStyle.MARKET:
        self._execute_market_order(order)
```

### 2. app/services/trade_service.py - Trade Execution
**Purpose**: Handles trade execution logic and trade history management.

**Key Responsibilities**:
- **Market Order Execution**: Immediate execution at current market price
- **Limit Order Execution**: Conditional execution based on price criteria
- **Portfolio Updates**: Updates portfolio positions when trades execute
- **Trade History**: Maintains record of all executed trades

**Execution Logic**:
```python
def execute_market_order(self, order: Order) -> Trade:
    instrument = self.storage.get_instrument(order.symbol)
    execution_price = instrument.last_traded_price
    trade = Trade.create(order, execution_price)
    
    # Update order status and portfolio
    self.storage.update_order_status(order.id, OrderStatus.EXECUTED)
    quantity_change = order.quantity if order.order_type.value == "BUY" else -order.quantity
    self.storage.update_portfolio_position(order.symbol, quantity_change, execution_price)
```

### 3. app/services/portfolio_service.py - Portfolio Management
**Purpose**: Manages portfolio calculations and position tracking.

**Key Responsibilities**:
- **Position Calculation**: Calculates current portfolio positions
- **Average Price Calculation**: Maintains weighted average prices
- **Current Value Calculation**: Updates positions with current market prices
- **Portfolio Retrieval**: Provides current portfolio state

### 4. app/services/instrument_service.py - Instrument Management
**Purpose**: Manages available financial instruments.

**Key Responsibilities**:
- **Instrument Retrieval**: Provides list of available instruments
- **Instrument Validation**: Validates instrument symbols
- **Price Information**: Maintains current market prices

## API Routes

### 1. app/routes/orders.py - Order Endpoints
**Endpoints**:
- `POST /api/v1/orders` - Place new order (returns 201 Created)
- `GET /api/v1/orders/{order_id}` - Get order status

**Features**:
- Automatic validation using Pydantic schemas
- Proper HTTP status codes
- Comprehensive error handling

### 2. app/routes/trades.py - Trade Endpoints
**Endpoints**:
- `GET /api/v1/trades` - List all executed trades

**Features**:
- Returns complete trade history
- Includes order references for traceability

### 3. app/routes/portfolio.py - Portfolio Endpoints
**Endpoints**:
- `GET /api/v1/portfolio` - Get current portfolio holdings

**Features**:
- Real-time portfolio calculations
- Includes average prices and current values

### 4. app/routes/instruments.py - Instrument Endpoints
**Endpoints**:
- `GET /api/v1/instruments` - List available instruments

**Features**:
- Returns all tradeable instruments with current prices

## Testing Architecture

### 1. tests/unit/ - Unit Tests
**Purpose**: Test individual components in isolation.

**Test Files**:
- `test_orders.py` - Order service unit tests
- `test_trades.py` - Trade service unit tests
- `test_portfolio.py` - Portfolio service unit tests
- `test_storage.py` - Storage layer unit tests
- `test_*_endpoints.py` - API endpoint unit tests

### 2. tests/integration/ - Integration Tests
**Purpose**: Test complete workflows end-to-end.

**Key Test File**:
- `test_end_to_end.py` - Complete trading workflows
  - Place order → Execute → Update portfolio
  - Multiple instrument trading
  - Error handling across endpoints
  - System health monitoring

### 3. tests/property/ - Property-Based Tests
**Purpose**: Test universal properties using Hypothesis library.

**Test Files**:
- `test_order_validation.py` - Order validation properties
- `test_order_api.py` - API behavior properties
- `test_error_handling.py` - Error handling consistency
- `test_trade_service.py` - Trade execution properties
- `test_portfolio_service.py` - Portfolio calculation properties

**Property Examples**:
```python
@given(invalid_quantity=st.integers(max_value=0))
def test_error_handling_consistency_invalid_input(self, invalid_quantity):
    # Tests that any invalid quantity returns proper error response
```

## Data Flow Architecture

### 1. Request Flow
```
HTTP Request → FastAPI → Route Handler → Service Layer → Storage Layer → Response
```

### 2. Order Placement Flow
```
OrderRequest → Validation → Order Creation → Storage → Market Order Auto-Execution → Trade Creation → Portfolio Update
```

### 3. Error Handling Flow
```
Exception → Custom Exception Handler → Error Response Creation → HTTP Response with Proper Status Code
```

## Key Design Patterns

### 1. Repository Pattern
- Storage layer abstracts data access
- Services interact with storage interface
- Easy to swap storage implementations

### 2. Service Layer Pattern
- Business logic separated from API routes
- Each domain has dedicated service
- Services can interact with each other

### 3. Exception Handling Pattern
- Custom exceptions with error codes
- Global exception handlers
- Consistent error response format

### 4. Factory Pattern
- Model creation through factory methods
- Ensures proper initialization
- Generates unique IDs automatically

## Configuration and Dependencies

### requirements.txt
```
fastapi==0.104.1          # Web framework
uvicorn==0.24.0           # ASGI server
pydantic==2.5.0           # Data validation
pytest==7.4.3            # Testing framework
hypothesis==6.88.1        # Property-based testing
httpx==0.25.2             # HTTP client for testing
```

## Security Considerations

### 1. Input Validation
- All inputs validated using Pydantic schemas
- Type checking and constraint validation
- SQL injection prevention (no SQL used)

### 2. Error Handling
- No sensitive information in error messages
- Consistent error response format
- Proper HTTP status codes

### 3. Thread Safety
- All storage operations are thread-safe
- Concurrent request handling supported
- No race conditions in portfolio updates

## Performance Considerations

### 1. In-Memory Storage
- Fast read/write operations
- No database overhead
- Suitable for development/testing

### 2. Thread Safety
- Minimal locking overhead
- RLock allows recursive locking
- Efficient concurrent access

### 3. Validation
- Pydantic provides fast validation
- Early validation prevents processing invalid data
- Minimal computational overhead

## Extensibility Points

### 1. Storage Layer
- Easy to replace with database implementation
- Interface-based design allows swapping
- Current implementation serves as reference

### 2. Service Layer
- New services can be added easily
- Services can be extended with new methods
- Clear separation of concerns

### 3. API Routes
- New endpoints can be added
- Existing endpoints can be versioned
- Consistent patterns for new routes

### 4. Exception Handling
- New exception types can be added
- Error codes can be extended
- Custom handling for specific errors

This architecture provides a solid foundation for a production trading system while maintaining simplicity for development and testing purposes.