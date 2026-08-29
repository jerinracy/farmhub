from datetime import date
from typing import List, Optional
from pydantic import BaseModel


class CurrentUser(BaseModel):
    id: int
    username: str
    role: str


class FarmInfo(BaseModel):
    id: int
    name: str


class FarmerInfo(BaseModel):
    id: int
    username: str


class PerCowBreakdown(BaseModel):
    tag_id: str
    total_liters: float


class PerFarmBreakdown(BaseModel):
    farm_id: int
    farm_name: str
    total_liters: float


class FarmReportResponse(BaseModel):
    farm: FarmInfo
    total_liters: float
    record_count: int
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    per_cow: List[PerCowBreakdown]


class FarmerReportResponse(BaseModel):
    farmer: FarmerInfo
    farm: Optional[str] = None
    total_liters: float
    record_count: int
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    per_cow: List[PerCowBreakdown]


class SummaryReportResponse(BaseModel):
    total_liters: float
    record_count: int
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    per_farm: List[PerFarmBreakdown]
