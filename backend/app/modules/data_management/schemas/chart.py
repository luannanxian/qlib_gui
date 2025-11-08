"""Chart Schemas for Data Management Module"""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from app.modules.data_management.models.chart import ChartType


class ChartConfigCreate(BaseModel):
    """Schema for creating a new chart configuration"""
    name: str
    chart_type: ChartType
    dataset_id: str
    config: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None


class ChartConfigUpdate(BaseModel):
    """Schema for updating a chart configuration"""
    name: Optional[str] = None
    chart_type: Optional[ChartType] = None
    config: Optional[Dict[str, Any]] = None
    description: Optional[str] = None


class ChartConfigResponse(BaseModel):
    """Schema for chart configuration response"""
    id: str
    name: str
    chart_type: ChartType
    dataset_id: str
    config: Dict[str, Any]
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChartConfigListResponse(BaseModel):
    """Schema for chart configuration list response"""
    total: int
    items: List[ChartConfigResponse]


# Technical Indicator Configuration Schemas

class MACDConfig(BaseModel):
    """MACD indicator configuration"""
    fast_period: int = Field(default=12, ge=1, le=100)
    slow_period: int = Field(default=26, ge=1, le=200)
    signal_period: int = Field(default=9, ge=1, le=50)

    @validator('slow_period')
    def slow_must_be_greater_than_fast(cls, v, values):
        if 'fast_period' in values and v <= values['fast_period']:
            raise ValueError('slow_period must be greater than fast_period')
        return v


class RSIConfig(BaseModel):
    """RSI indicator configuration"""
    period: int = Field(default=14, ge=2, le=100)
    overbought: float = Field(default=70, ge=50, le=100)
    oversold: float = Field(default=30, ge=0, le=50)

    @validator('oversold')
    def oversold_must_be_less_than_overbought(cls, v, values):
        if 'overbought' in values and v >= values['overbought']:
            raise ValueError('oversold must be less than overbought')
        return v


class KDJConfig(BaseModel):
    """KDJ indicator configuration"""
    k_period: int = Field(default=9, ge=1, le=100)
    d_period: int = Field(default=3, ge=1, le=50)
    j_period: int = Field(default=3, ge=1, le=50)


class MAConfig(BaseModel):
    """Moving Average configuration"""
    periods: List[int] = Field(default=[5, 10, 20, 60])

    @validator('periods')
    def validate_periods(cls, v):
        if not v:
            raise ValueError('At least one period must be specified')
        if any(p < 1 or p > 500 for p in v):
            raise ValueError('Period must be between 1 and 500')
        return sorted(v)  # Return sorted periods


class IndicatorRequest(BaseModel):
    """Request schema for indicator calculations"""
    indicators: Optional[List[str]] = Field(default=None, max_items=3)
    macd_params: Optional[MACDConfig] = None
    rsi_params: Optional[RSIConfig] = None
    kdj_params: Optional[KDJConfig] = None
    ma_params: Optional[MAConfig] = None

    @validator('indicators')
    def validate_indicators(cls, v):
        if v is None:
            return v
        valid_indicators = {'MACD', 'RSI', 'KDJ', 'MA', 'VOLUME'}
        for indicator in v:
            if indicator not in valid_indicators:
                raise ValueError(f'Invalid indicator: {indicator}. Valid: {valid_indicators}')
        return v


# Chart Data Request/Response Schemas

class ChartDataRequest(BaseModel):
    """Request schema for chart data generation"""
    dataset_id: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    indicators: Optional[List[str]] = Field(default=None, max_items=3)
    indicator_params: Optional[IndicatorRequest] = None
    chart_format: str = Field(default="ohlc")  # "ohlc" or "candlestick"

    @validator('chart_format')
    def validate_chart_format(cls, v):
        if v not in ['ohlc', 'candlestick']:
            raise ValueError('chart_format must be "ohlc" or "candlestick"')
        return v

    @validator('end_date')
    def end_date_after_start_date(cls, v, values):
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError('end_date must be after start_date')
        return v


class OHLCData(BaseModel):
    """OHLC data point"""
    date: Union[datetime, str]
    open: float
    high: float
    low: float
    close: float
    volume: Optional[int] = None


class ChartDataResponse(BaseModel):
    """Response schema for chart data"""
    dataset_id: str
    data: Union[List[OHLCData], List[List], Dict[str, Any]]
    indicators: Optional[Dict[str, Any]] = None
    annotations: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


# Annotation Schemas

class TextAnnotation(BaseModel):
    """Text annotation schema"""
    type: str = "text"
    date: datetime
    text: str
    position: str = Field(default="top")  # top, bottom, left, right

    @validator('position')
    def validate_position(cls, v):
        if v not in ['top', 'bottom', 'left', 'right']:
            raise ValueError('position must be one of: top, bottom, left, right')
        return v


class MarkerAnnotation(BaseModel):
    """Marker annotation schema"""
    type: str = "marker"
    date: datetime
    label: str
    color: Optional[str] = Field(default="red")


class AnnotationRequest(BaseModel):
    """Request schema for adding annotation"""
    chart_id: str
    annotation: Union[TextAnnotation, MarkerAnnotation]


# Export Schemas

class ChartExportRequest(BaseModel):
    """Request schema for chart data export"""
    chart_id: str
    format: str = Field(default="csv")  # csv, json, excel
    include_indicators: bool = Field(default=True)
    columns: Optional[List[str]] = None

    @validator('format')
    def validate_format(cls, v):
        if v not in ['csv', 'json', 'excel']:
            raise ValueError('format must be one of: csv, json, excel')
        return v


class ChartExportResponse(BaseModel):
    """Response schema for chart data export"""
    chart_id: str
    format: str
    data: str  # CSV string, JSON string, or base64 encoded Excel
    filename: str
    size_bytes: int
