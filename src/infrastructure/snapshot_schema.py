"""Pydantic schema for the on-disk snapshot format (source-agnostic)."""

from __future__ import annotations

from pydantic import BaseModel


class SnapshotVehicle(BaseModel):
    id: str
    source: str
    model: str
    title: str
    trim: str
    year: int
    odometer: int
    price: int
    paint: str
    autopilot: str
    city: str
    link: str


class SnapshotData(BaseModel):
    checked_at: str
    vehicles: list[SnapshotVehicle]
