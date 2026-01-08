from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas import TradeResponse
from app.services.trade_service import trade_service

router = APIRouter()

@router.get("/trades", response_model=List[TradeResponse])
async def get_trades():
    try:
        trades = trade_service.get_all_trades()
        return [
            TradeResponse(
                id=trade.id,
                order_id=trade.order_id,
                symbol=trade.symbol,
                quantity=trade.quantity,
                price=trade.price,
                executed_at=trade.executed_at
            )
            for trade in trades
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Failed to retrieve trades"
            }
        })

