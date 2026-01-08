# Trading API SDK - Complete Setup and Testing Guide

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Installation Guide](#installation-guide)
3. [Running the Application](#running-the-application)
4. [API Testing Guide](#api-testing-guide)
5. [Test Suite Execution](#test-suite-execution)
6. [Health Monitoring](#health-monitoring)
7. [Troubleshooting](#troubleshooting)
8. [Development Workflow](#development-workflow)

## System Requirements

### Minimum Requirements
- **Python**: 3.8 or higher
- **RAM**: 512MB available memory
- **Disk Space**: 100MB for dependencies
- **Network**: Internet connection for package installation

### Recommended Requirements
- **Python**: 3.9+ (for better performance)
- **RAM**: 1GB+ available memory
- **CPU**: 2+ cores for concurrent testing
- **OS**: Linux, macOS, or Windows 10+

### Required Tools
```bash
# Check Python version
python --version  # Should be 3.8+

# Check pip availability
pip --version

# Optional but recommended
curl --version    # For API testing
jq --version      # For JSON formatting (optional)
```

## Installation Guide

### Step 1: Clone/Download the Project
```bash
# If using git
git clone <repository-url>
cd trading-api-sdk

# Or extract from ZIP file
unzip trading-api-sdk.zip
cd trading-api-sdk
```

### Step 2: Create Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Verify activation (should show venv path)
which python
```

### Step 3: Install Dependencies
```bash
# Install all required packages
pip install -r requirements.txt

# Verify installation
pip list | grep fastapi
pip list | grep uvicorn
pip list | grep pytest
pip list | grep hypothesis
```

### Step 4: Verify Installation
```bash
# Quick verification
python -c "import fastapi, uvicorn, pytest, hypothesis; print('All dependencies installed successfully!')"
```

## Running the Application

### Method 1: Using Uvicorn (Recommended)
```bash
# Start the development server
uvicorn app.main:app --reload

# Server will start on http://localhost:8000
# --reload enables auto-restart on code changes
```

### Method 2: Using Python Module
```bash
# Alternative method
python -m uvicorn app.main:app --reload
```

### Method 3: Custom Host/Port
```bash
# Run on different host/port
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# Run without reload (production-like)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Verify Server is Running
```bash
# Check health endpoint
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "service": "Trading API SDK",
  "version": "1.0.0",
  "timestamp": "2024-01-XX...",
  "system_stats": {
    "instruments_loaded": 5,
    "total_orders": 0,
    "total_trades": 0,
    "portfolio_positions": 0
  },
  "components": {
    "storage": "operational",
    "order_service": "operational",
    "trade_service": "operational",
    "portfolio_service": "operational"
  }
}
```

## API Testing Guide

### Interactive Documentation
```bash
# Open in browser
# Swagger UI (recommended)
http://localhost:8000/docs

# ReDoc (alternative)
http://localhost:8000/redoc

# OpenAPI JSON schema
http://localhost:8000/openapi.json
```

### Manual API Testing

#### 1. Get Available Instruments
```bash
# List all instruments
curl -X GET "http://localhost:8000/api/v1/instruments" \
  -H "accept: application/json"

# Expected response:
[
  {
    "symbol": "TCS",
    "exchange": "NSE",
    "instrument_type": "STOCK",
    "last_traded_price": "3450.25"
  },
  {
    "symbol": "INFY",
    "exchange": "NSE",
    "instrument_type": "STOCK",
    "last_traded_price": "1520.40"
  },
  ...
]
```

#### 2. Place Market Order
```bash
# Place a BUY market order
curl -X POST "http://localhost:8000/api/v1/orders" \
  -H "Content-Type: application/json" \
  -H "accept: application/json" \
  -d '{
    "symbol": "TCS",
    "order_type": "BUY",
    "order_style": "MARKET",
    "quantity": 10
  }'

# Expected response (201 Created):
{
  "id": "uuid-string",
  "symbol": "TCS",
  "order_type": "BUY",
  "order_style": "MARKET",
  "quantity": 10,
  "price": null,
  "status": "EXECUTED",
  "created_at": "2024-01-XX..."
}
```

#### 3. Place Limit Order
```bash
# Place a SELL limit order
curl -X POST "http://localhost:8000/api/v1/orders" \
  -H "Content-Type: application/json" \
  -H "accept: application/json" \
  -d '{
    "symbol": "INFY",
    "order_type": "SELL",
    "order_style": "LIMIT",
    "quantity": 5,
    "price": 1500.00
  }'

# Expected response (201 Created):
{
  "id": "uuid-string",
  "symbol": "INFY",
  "order_type": "SELL",
  "order_style": "LIMIT",
  "quantity": 5,
  "price": "1500.00",
  "status": "PLACED",
  "created_at": "2024-01-XX..."
}
```

#### 4. Check Order Status
```bash
# Get order status (replace {order_id} with actual ID)
curl -X GET "http://localhost:8000/api/v1/orders/{order_id}" \
  -H "accept: application/json"

# Example:
curl -X GET "http://localhost:8000/api/v1/orders/123e4567-e89b-12d3-a456-426614174000" \
  -H "accept: application/json"
```

#### 5. View Trade History
```bash
# Get all executed trades
curl -X GET "http://localhost:8000/api/v1/trades" \
  -H "accept: application/json"

# Expected response:
[
  {
    "id": "trade-uuid",
    "order_id": "order-uuid",
    "symbol": "TCS",
    "quantity": 10,
    "price": "3450.25",
    "executed_at": "2024-01-XX..."
  }
]
```

#### 6. Check Portfolio
```bash
# Get current portfolio holdings
curl -X GET "http://localhost:8000/api/v1/portfolio" \
  -H "accept: application/json"

# Expected response:
[
  {
    "symbol": "TCS",
    "quantity": 10,
    "average_price": "3450.25",
    "current_value": "34502.50"
  }
]
```

### Error Testing

#### 1. Invalid Symbol
```bash
curl -X POST "http://localhost:8000/api/v1/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "INVALID",
    "order_type": "BUY",
    "order_style": "MARKET",
    "quantity": 10
  }'

# Expected: 404 Not Found
{
  "error": {
    "code": "INSTRUMENT_NOT_FOUND",
    "message": "Instrument INVALID not found"
  }
}
```

#### 2. Invalid Quantity
```bash
curl -X POST "http://localhost:8000/api/v1/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "TCS",
    "order_type": "BUY",
    "order_style": "MARKET",
    "quantity": 0
  }'

# Expected: 422 Unprocessable Entity
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "validation_errors": [
        {
          "field": "body.quantity",
          "message": "Input should be greater than 0",
          "type": "greater_than"
        }
      ]
    }
  }
}
```

#### 3. Limit Order Without Price
```bash
curl -X POST "http://localhost:8000/api/v1/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "TCS",
    "order_type": "BUY",
    "order_style": "LIMIT",
    "quantity": 10
  }'

# Expected: 400 Bad Request
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Price is required for limit orders"
  }
}
```

## Test Suite Execution

### Running All Tests
```bash
# Run complete test suite
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=app

# Run with detailed coverage
pytest --cov=app --cov-report=html
```

### Running Specific Test Categories

#### 1. Unit Tests
```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific unit test file
pytest tests/unit/test_orders.py -v

# Run specific test method
pytest tests/unit/test_orders.py::TestOrderService::test_place_market_order_success -v
```

#### 2. Integration Tests
```bash
# Run all integration tests
pytest tests/integration/ -v

# Run specific integration test
pytest tests/integration/test_end_to_end.py::TestEndToEndWorkflows::test_complete_trading_workflow -v
```

#### 3. Property-Based Tests
```bash
# Run all property tests
pytest tests/property/ -v

# Run specific property test file
pytest tests/property/test_error_handling.py -v

# Run property tests with more examples
pytest tests/property/ -v --hypothesis-max-examples=1000
```

### Test Output Interpretation

#### Successful Test Run
```bash
$ pytest -v
========================= test session starts =========================
platform darwin -- Python 3.9.7, pytest-7.4.3
collected 121 items

tests/unit/test_orders.py::TestOrderService::test_place_market_order_success PASSED [  1%]
tests/unit/test_orders.py::TestOrderService::test_place_limit_order_success PASSED [  2%]
...
tests/integration/test_end_to_end.py::TestEndToEndWorkflows::test_complete_trading_workflow PASSED [ 98%]
tests/property/test_error_handling.py::TestErrorHandlingProperties::test_error_handling_consistency PASSED [100%]

========================= 121 passed in 15.23s =========================
```

#### Failed Test Example
```bash
FAILED tests/unit/test_orders.py::TestOrderService::test_invalid_symbol - AssertionError: Expected exception not raised

========================= FAILURES =========================
_ TestOrderService.test_invalid_symbol _

    def test_invalid_symbol(self):
        with pytest.raises(InstrumentNotFoundError):
>           order_service.place_order(invalid_order_request)
E           AssertionError: InstrumentNotFoundError not raised

tests/unit/test_orders.py:45: AssertionError
========================= 1 failed, 120 passed in 12.34s =========================
```

### Performance Testing
```bash
# Run tests with timing information
pytest --durations=10

# Run tests in parallel (if pytest-xdist installed)
pip install pytest-xdist
pytest -n auto

# Memory usage testing
pip install pytest-memray
pytest --memray
```

## Health Monitoring

### System Health Check
```bash
# Basic health check
curl http://localhost:8000/health

# Health check with formatted output
curl -s http://localhost:8000/health | python -m json.tool
```

### Monitoring During Load
```bash
# Simple load test script
for i in {1..10}; do
  curl -X POST "http://localhost:8000/api/v1/orders" \
    -H "Content-Type: application/json" \
    -d "{\"symbol\": \"TCS\", \"order_type\": \"BUY\", \"order_style\": \"MARKET\", \"quantity\": $i}" &
done
wait

# Check system stats after load
curl -s http://localhost:8000/health | jq '.system_stats'
```

### Log Monitoring
```bash
# View application logs (if running with file logging)
tail -f trading_api.log

# Filter for errors
tail -f trading_api.log | grep ERROR

# Monitor startup logs
uvicorn app.main:app --reload | grep "Trading API"
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Port Already in Use
```bash
# Error: "Address already in use"
# Solution: Use different port
uvicorn app.main:app --port 8001 --reload

# Or kill existing process
lsof -ti:8000 | xargs kill -9
```

#### 2. Module Import Errors
```bash
# Error: "ModuleNotFoundError: No module named 'app'"
# Solution: Ensure you're in the correct directory
pwd  # Should show trading-api-sdk directory
ls   # Should show app/ directory

# Or set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### 3. Permission Errors
```bash
# Error: "Permission denied"
# Solution: Check file permissions
chmod +x requirements.txt
chmod -R 755 app/

# Or run with sudo (not recommended)
sudo uvicorn app.main:app --reload
```

#### 4. Dependency Conflicts
```bash
# Error: "Dependency conflicts"
# Solution: Create fresh virtual environment
deactivate
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 5. Test Failures
```bash
# Error: "Tests failing unexpectedly"
# Solution: Clear Python cache
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete

# Reinstall in development mode
pip install -e .
```

### Debug Mode
```bash
# Run with debug logging
uvicorn app.main:app --reload --log-level debug

# Run tests with debug output
pytest -v -s --tb=long

# Python debugger in tests
pytest --pdb
```

## Development Workflow

### Setting Up Development Environment
```bash
# 1. Clone and setup
git clone <repo>
cd trading-api-sdk
python -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install development dependencies (optional)
pip install black isort flake8 mypy

# 4. Run initial tests
pytest

# 5. Start development server
uvicorn app.main:app --reload
```

### Code Quality Checks
```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Lint code
flake8 app/ tests/

# Type checking
mypy app/
```

### Pre-commit Checklist
```bash
# 1. Run all tests
pytest

# 2. Check code quality
black --check app/ tests/
flake8 app/ tests/

# 3. Verify API works
curl http://localhost:8000/health

# 4. Test key endpoints
curl -X POST "http://localhost:8000/api/v1/orders" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "TCS", "order_type": "BUY", "order_style": "MARKET", "quantity": 1}'
```

### Performance Monitoring
```bash
# Monitor memory usage
ps aux | grep uvicorn

# Monitor API response times
time curl http://localhost:8000/api/v1/instruments

# Load testing with ab (Apache Bench)
ab -n 100 -c 10 http://localhost:8000/health
```

## Production Deployment Considerations

### Environment Variables
```bash
# Set production environment
export ENVIRONMENT=production
export LOG_LEVEL=INFO
export HOST=0.0.0.0
export PORT=8000
```

### Production Server
```bash
# Install production server
pip install gunicorn

# Run with gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

# With specific configuration
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### Docker Deployment
```dockerfile
# Dockerfile example
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

This comprehensive guide covers all aspects of setting up, running, and testing the Trading API SDK. Follow the steps in order for the best experience, and refer to the troubleshooting section if you encounter any issues.