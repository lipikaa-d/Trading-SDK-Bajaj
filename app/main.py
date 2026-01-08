from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from app.routes import orders, trades, instruments, portfolio
from app.exceptions import TradingAPIException, create_error_response, get_http_status_for_error
from app.storage import storage
import logging
import sys

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('trading_api.log')
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Trading API SDK",
    description="A comprehensive trading API wrapper for managing instruments, orders, trades, and portfolio",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting Trading API SDK...")
    
    # Initialize sample data
    instruments_count = len(storage.get_all_instruments())
    logger.info(f"Loaded {instruments_count} sample instruments")
    
    # Log system status
    logger.info("Trading API SDK startup complete")
    logger.info("Available endpoints:")
    logger.info("  GET /api/v1/instruments - List all instruments")
    logger.info("  POST /api/v1/orders - Place new order")
    logger.info("  GET /api/v1/orders/{order_id} - Get order status")
    logger.info("  GET /api/v1/trades - List all trades")
    logger.info("  GET /api/v1/portfolio - Get portfolio holdings")
    logger.info("  GET /health - Health check")
    logger.info("  GET /docs - API documentation")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("Shutting down Trading API SDK...")
    
    # Log final statistics
    orders_count = len(storage.get_all_orders())
    trades_count = len(storage.get_all_trades())
    portfolio_positions = len(storage.get_portfolio_holdings())
    
    logger.info(f"Final statistics:")
    logger.info(f"  Total orders processed: {orders_count}")
    logger.info(f"  Total trades executed: {trades_count}")
    logger.info(f"  Portfolio positions: {portfolio_positions}")
    logger.info("Trading API SDK shutdown complete")

@app.exception_handler(TradingAPIException)
async def trading_api_exception_handler(request: Request, exc: TradingAPIException):
    """Handle custom trading API exceptions"""
    logger.error(f"Trading API error: {exc.error_code} - {exc.message}")
    
    status_code = get_http_status_for_error(exc.error_code)
    error_response = create_error_response(exc.error_code, exc.message)
    
    return JSONResponse(
        status_code=status_code,
        content=error_response
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    logger.error(f"Validation error: {exc.errors()}")
    
    # Extract field information from validation errors
    error_details = []
    for error in exc.errors():
        error_details.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    error_response = create_error_response(
        "VALIDATION_ERROR",
        "Request validation failed",
        {"validation_errors": error_details}
    )
    
    return JSONResponse(
        status_code=422,
        content=error_response
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions"""
    logger.error(f"Value error: {str(exc)}")
    
    error_response = create_error_response(
        "VALIDATION_ERROR",
        str(exc)
    )
    
    return JSONResponse(
        status_code=400,
        content=error_response
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    logger.error(f"Unexpected error: {type(exc).__name__} - {str(exc)}", exc_info=True)
    
    error_response = create_error_response(
        "INTERNAL_SERVER_ERROR",
        "An unexpected error occurred"
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response
    )

@app.get("/health")
async def health_check():
    """Health check endpoint with system status"""
    try:
        # Check system components
        instruments_count = len(storage.get_all_instruments())
        orders_count = len(storage.get_all_orders())
        trades_count = len(storage.get_all_trades())
        portfolio_positions = len(storage.get_portfolio_holdings())
        
        return {
            "status": "healthy",
            "service": "Trading API SDK",
            "version": "1.0.0",
            "timestamp": storage.get_current_timestamp(),
            "system_stats": {
                "instruments_loaded": instruments_count,
                "total_orders": orders_count,
                "total_trades": trades_count,
                "portfolio_positions": portfolio_positions
            },
            "components": {
                "storage": "operational",
                "order_service": "operational",
                "trade_service": "operational",
                "portfolio_service": "operational"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "Trading API SDK",
                "version": "1.0.0",
                "error": str(e)
            }
        )

# Include routers
app.include_router(instruments.router, prefix="/api/v1", tags=["instruments"])
app.include_router(orders.router, prefix="/api/v1", tags=["orders"])
app.include_router(trades.router, prefix="/api/v1", tags=["trades"])
app.include_router(portfolio.router, prefix="/api/v1", tags=["portfolio"])
