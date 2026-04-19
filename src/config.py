from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SearchConfig:
    zip_code: str = "59130"
    latitude: float = 50.6117
    longitude: float = 3.1665
    market: str = "FR"
    language: str = "fr"
    model: str = "m3"
    condition: str = "used"
    min_year: int = 2024
    max_odometer: int = 50000
    paints: tuple[str, ...] = ("WHITE", "BLACK")
    trims: tuple[str, ...] = ("LRAWD", "PRAWD", "PAWD")
    require_enhanced_autopilot: bool = True


@dataclass(frozen=True)
class NotifyConfig:
    topic: str = ""
    base_url: str = "https://ntfy.sh"


@dataclass(frozen=True)
class AppConfig:
    results_dir: str = "/data"
    search: SearchConfig = field(default_factory=SearchConfig)
    notify: NotifyConfig = field(default_factory=NotifyConfig)


def load_config() -> AppConfig:
    paints_raw = os.environ.get("TESLA_PAINTS", "")
    trims_raw = os.environ.get("TESLA_TRIMS", "")

    search = SearchConfig(
        zip_code=os.environ.get("TESLA_ZIP", SearchConfig.zip_code),
        latitude=float(os.environ.get("TESLA_LAT", str(SearchConfig.latitude))),
        longitude=float(os.environ.get("TESLA_LNG", str(SearchConfig.longitude))),
        market=os.environ.get("TESLA_MARKET", SearchConfig.market),
        language=os.environ.get("TESLA_LANGUAGE", SearchConfig.language),
        model=os.environ.get("TESLA_MODEL", SearchConfig.model),
        condition=os.environ.get("TESLA_CONDITION", SearchConfig.condition),
        min_year=int(os.environ.get("TESLA_MIN_YEAR", str(SearchConfig.min_year))),
        max_odometer=int(os.environ.get("TESLA_MAX_ODOMETER", str(SearchConfig.max_odometer))),
        paints=tuple(paints_raw.split(",")) if paints_raw else SearchConfig.paints,
        trims=tuple(trims_raw.split(",")) if trims_raw else SearchConfig.trims,
        require_enhanced_autopilot=os.environ.get(
            "TESLA_REQUIRE_EAP", "true"
        ).lower() == "true",
    )

    notify = NotifyConfig(
        topic=os.environ.get("NTFY_TOPIC", NotifyConfig.topic),
        base_url=os.environ.get("NTFY_URL", NotifyConfig.base_url),
    )

    return AppConfig(
        results_dir=os.environ.get("RESULTS_DIR", AppConfig.results_dir),
        search=search,
        notify=notify,
    )
