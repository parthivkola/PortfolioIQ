from pydantic import BaseModel


class SearchResult(BaseModel):
    symbol: str
    name: str
    asset_type: str


class QuoteResponse(BaseModel):
    symbol: str
    price: str
    as_of: str
    source: str


class HistoryPoint(BaseModel):
    date: str
    close: str


class HistoryResponse(BaseModel):
    symbol: str
    range: str
    points: list[HistoryPoint]
