from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas import InstrumentResponse
from app.services.instrument_service import instrument_service

router = APIRouter()

@router.get("/instruments", response_model=List[InstrumentResponse])
async def get_instruments():
    try:
        instruments = instrument_service.get_all_instruments()
        return [
            InstrumentResponse(
                symbol=inst.symbol,
                exchange=inst.exchange,
                instrument_type=inst.instrument_type,
                last_traded_price=inst.last_traded_price
            )
            for inst in instruments
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve instruments")
