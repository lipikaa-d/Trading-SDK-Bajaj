from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas import PortfolioResponse
from app.services.portfolio_service import portfolio_service

router = APIRouter()

@router.get("/portfolio", response_model=List[PortfolioResponse])
async def get_portfolio():
    try:
        holdings = portfolio_service.get_portfolio()
        return [
            PortfolioResponse(
                symbol=holding.symbol,
                quantity=holding.quantity,
                average_price=holding.average_price,
                current_value=holding.current_value
            )
            for holding in holdings
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Failed to retrieve portfolio"
            }
        })