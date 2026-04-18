from datetime import datetime

import pytest

from src.domain.vehicle import Paint, Trim, Vehicle


@pytest.fixture
def white_prawd_2024() -> Vehicle:
    return Vehicle(
        vin="LRW3E7EK2RC971169",
        title="Premium Grande Autonomie Transmission intégrale",
        trim=Trim.PRAWD,
        year=2024,
        odometer=29752,
        price=40100,
        paint=Paint.WHITE,
        has_enhanced_autopilot=True,
        city="Bailly-Romainvilliers",
    )


@pytest.fixture
def black_pawd_2024() -> Vehicle:
    return Vehicle(
        vin="LRW3E7ET8RC170223",
        title="Performance Transmission Intégrale",
        trim=Trim.PAWD,
        year=2024,
        odometer=25203,
        price=48700,
        paint=Paint.BLACK,
        has_enhanced_autopilot=True,
        city="Saint-Priest",
    )


@pytest.fixture
def white_pawd_2025() -> Vehicle:
    return Vehicle(
        vin="LRW3E7ET4SC510781",
        title="Performance Transmission Intégrale",
        trim=Trim.PAWD,
        year=2025,
        odometer=10476,
        price=52700,
        paint=Paint.WHITE,
        has_enhanced_autopilot=True,
        city="Plaisance-du-Touch",
    )


@pytest.fixture
def now() -> datetime:
    return datetime(2026, 4, 18, 12, 0, 0)
