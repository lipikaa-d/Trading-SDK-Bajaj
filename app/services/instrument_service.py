from typing import List
from app.models import Instrument
from app.storage import storage


class InstrumentService:
    def __init__(self):
        self.storage = storage
    
    def get_all_instruments(self) -> List[Instrument]:
        return self.storage.get_all_instruments()
    
    def get_instrument_by_symbol(self, symbol: str) -> Instrument:
        instrument = self.storage.get_instrument(symbol)
        if not instrument:
            raise ValueError(f"Instrument with symbol {symbol} not found")
        return instrument


instrument_service = InstrumentService()