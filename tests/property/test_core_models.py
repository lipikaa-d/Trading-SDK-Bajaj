import pytest
from hypothesis import given, strategies as st
from decimal import Decimal
from app.models import Instrument, InstrumentType


@given(
    symbol=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    exchange=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))),
    instrument_type=st.sampled_from(InstrumentType),
    price=st.decimals(min_value=Decimal('0.01'), max_value=Decimal('10000'), places=2)
)
def test_instrument_data_completeness(symbol, exchange, instrument_type, price):
    """
    Feature: trading-api-sdk, Property 1: Instrument Data Completeness
    For any instrument returned by the system, it should contain symbol, exchange, instrument_type, and last_traded_price fields
    """
    instrument = Instrument(
        symbol=symbol,
        exchange=exchange,
        instrument_type=instrument_type,
        last_traded_price=price
    )
    
    assert hasattr(instrument, 'symbol')
    assert hasattr(instrument, 'exchange')
    assert hasattr(instrument, 'instrument_type')
    assert hasattr(instrument, 'last_traded_price')
    
    assert instrument.symbol is not None
    assert instrument.exchange is not None
    assert instrument.instrument_type is not None
    assert instrument.last_traded_price is not None
    
    assert isinstance(instrument.symbol, str)
    assert isinstance(instrument.exchange, str)
    assert isinstance(instrument.instrument_type, InstrumentType)
    assert isinstance(instrument.last_traded_price, Decimal)