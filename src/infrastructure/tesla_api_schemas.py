"""Pydantic schemas for Tesla inventory API responses."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TeslaVehicleResult(BaseModel):
    VIN: str = ""
    TrimName: str = ""
    TRIM: list[str] = Field(default_factory=list)
    Year: int = 0
    Odometer: int = 0
    Price: int = 0
    PAINT: list[str] = Field(default_factory=list)
    AUTOPILOT: list[str] = Field(default_factory=list)
    City: str = ""


class TeslaInventoryResponse(BaseModel):
    total_matches_found: int = 0
    results: list[TeslaVehicleResult] = Field(default_factory=list)


class TeslaSnapshotVehicle(BaseModel):
    vin: str
    title: str
    trim: str
    year: int
    odometer: int
    price: int
    paint: str
    has_enhanced_autopilot: bool
    city: str


class TeslaSnapshotData(BaseModel):
    checked_at: str
    vehicles: list[TeslaSnapshotVehicle]
