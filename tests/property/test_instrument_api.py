import pytest
from hypothesis import given, strategies as st
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_instrument_api_data_completeness():
    """
    Feature: trading-api-sdk, Property 1: Instrument Data Completeness
    For any instrument returned by the system, it should contain symbol, exchange, instrument_type, and last_traded_price fields
    """
    response = client.get("/api/v1/instruments")
    assert response.status_code == 200
    
    instruments = response.json()
    assert isinstance(instruments, list)
    
    for instrument in instruments:
        assert "symbol" in instrument
        assert "exchange" in instrument
        assert "instrument_type" in instrument
        assert "last_traded_price" in instrument
        
        assert instrument["symbol"] is not None
        assert instrument["exchange"] is not None
        assert instrument["instrument_type"] is not None
        assert instrument["last_traded_price"] is not None
        
        assert isinstance(instrument["symbol"], str)
        assert isinstance(instrument["exchange"], str)
        assert isinstance(instrument["instrument_type"], str)
        assert isinstance(instrument["last_traded_price"], str)  # Decimal serialized as string