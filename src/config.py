from __future__ import annotations

import os
from dataclasses import dataclass, field

from src.domain.vehicle import Autopilot, Model, Paint, Trim


@dataclass(frozen=True)
class TeslaSearchConfig:
    """Tesla inventory search parameters (single model).

    Since 2026-05-21 Tesla no longer sells EAP/FSD outright — the used
    inventory only carries base Autopilot and FSD is offered as a separate
    subscription. We accept all autopilot tiers so the user gets pinged for
    any AWD M3 matching the rest of the criteria.
    """

    model: Model
    zip_code: str = "59130"
    latitude: float = 50.6117
    longitude: float = 3.1665
    market: str = "FR"
    language: str = "fr"
    condition: str = "used"
    min_year: int = 2024
    max_odometer: int = 50000
    paints: tuple[Paint, ...] = (Paint.WHITE, Paint.BLACK)
    trims: tuple[Trim, ...] = (Trim.LRAWD, Trim.PRAWD, Trim.PAWD)
    accepted_autopilots: tuple[Autopilot, ...] = (
        Autopilot.BASIC,
        Autopilot.ENHANCED,
        Autopilot.FSD,
    )


@dataclass(frozen=True)
class LeboncoinSearchConfig:
    """Leboncoin search parameters."""

    model: Model
    min_year: int = 2024
    max_odometer: int = 80000
    paints: tuple[Paint, ...] = (Paint.WHITE, Paint.BLACK)
    trims: tuple[Trim, ...] = (Trim.LRAWD, Trim.PRAWD, Trim.PAWD)
    accepted_autopilots: tuple[Autopilot, ...] = (Autopilot.ENHANCED, Autopilot.FSD)


@dataclass(frozen=True)
class NotifyConfig:
    topic: str = ""
    base_url: str = "https://ntfy.sh"


@dataclass(frozen=True)
class AppConfig:
    results_dir: str = "/data"
    tesla_m3: TeslaSearchConfig = field(
        default_factory=lambda: TeslaSearchConfig(model=Model.M3)
    )
    lbc_m3: LeboncoinSearchConfig = field(
        default_factory=lambda: LeboncoinSearchConfig(model=Model.M3)
    )
    lbc_my: LeboncoinSearchConfig = field(
        default_factory=lambda: LeboncoinSearchConfig(
            model=Model.MY,
            paints=(Paint.BLACK,),
        )
    )
    notify: NotifyConfig = field(default_factory=NotifyConfig)


def load_config() -> AppConfig:
    return AppConfig(
        results_dir=os.environ.get("RESULTS_DIR", AppConfig.results_dir),
        notify=NotifyConfig(
            topic=os.environ.get("NTFY_TOPIC", NotifyConfig.topic),
            base_url=os.environ.get("NTFY_URL", NotifyConfig.base_url),
        ),
    )
