from __future__ import annotations

import json
import logging
import urllib.parse
from collections.abc import Mapping

from camoufox import Camoufox
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page

from src.config import TeslaSearchConfig
from src.domain.vehicle import Autopilot, Model, Paint, Source, Trim, Vehicle
from src.infrastructure.tesla_api_schemas import TeslaInventoryResponse, TeslaVehicleResult

log = logging.getLogger(__name__)

_TRIM_MAP: dict[str, Trim] = {t.value: t for t in Trim}
_PAINT_MAP: dict[str, Paint] = {"WHITE": Paint.WHITE, "BLACK": Paint.BLACK}

_MODEL_CODE: dict[Model, str] = {Model.M3: "m3", Model.MY: "my"}


_FSD_CODE_HINTS = ("FSD", "AUTOPARK", "FULL_SELF_DRIVING")
_ENHANCED_CODE_HINTS = ("ENHANCED_AUTOPILOT", "EAP", "ENHANCED")
_KNOWN_AUTOPILOT_CODES = {
    "AUTOPILOT",
    "ENHANCED_AUTOPILOT",
    "FSD",
    "AUTOPARK",
    "FULL_SELF_DRIVING",
}


def _autopilot_from_codes(codes: list[str]) -> Autopilot:
    # Tesla can update AUTOPILOT codes (e.g. May 2026 dropped purchasable EAP/FSD
    # in favor of a subscription). Be tolerant: look for substrings rather than
    # exact matches, and log anything we don't recognize so we can extend the map.
    for code in codes:
        if code and code not in _KNOWN_AUTOPILOT_CODES:
            log.info(f"Unknown Tesla AUTOPILOT code seen: {code!r}")
    if any(h in code for code in codes for h in _FSD_CODE_HINTS):
        return Autopilot.FSD
    if any(h in code for code in codes for h in _ENHANCED_CODE_HINTS):
        return Autopilot.ENHANCED
    return Autopilot.BASIC


def _to_vehicle(r: TeslaVehicleResult, model: Model, language: str, market: str) -> Vehicle | None:
    trim_code = r.TRIM[0] if r.TRIM else ""
    paint_code = r.PAINT[0] if r.PAINT else ""

    trim = _TRIM_MAP.get(trim_code)
    paint = _PAINT_MAP.get(paint_code, Paint.OTHER)
    if trim is None:
        return None

    model_code = _MODEL_CODE[model]
    link = f"https://www.tesla.com/{language}_{market.lower()}/{model_code}/order/{r.VIN}"

    return Vehicle(
        id=r.VIN,
        source=Source.TESLA,
        model=model,
        title=r.TrimName,
        trim=trim,
        year=r.Year,
        odometer=r.Odometer,
        price=r.Price,
        paint=paint,
        autopilot=_autopilot_from_codes(r.AUTOPILOT),
        city=r.City,
        link=link,
    )


def _build_inventory_url(config: TeslaSearchConfig) -> str:
    paints = ",".join(p.value for p in config.paints)
    model_code = _MODEL_CODE[config.model]
    return (
        f"https://www.tesla.com/{config.language}_{config.market.lower()}"
        f"/inventory/{config.condition}/{model_code}"
        f"?arrangeby=plh&zip={config.zip_code}&range=0"
        f"&PAINT={paints}&AUTOPILOT=ENHANCED_AUTOPILOT"
    )


def _build_api_query(config: TeslaSearchConfig) -> dict[str, object]:
    years = list(range(config.min_year, 2027))
    model_code = _MODEL_CODE[config.model]
    # Tesla revised its purchase options in May 2026 (no more buying EAP/FSD
    # outright, FSD subscription only). The AUTOPILOT filter code may not be
    # accepted anymore, so we no longer constrain on it server-side — the
    # client-side SearchCriteria filter still keeps the user's preferences.
    return {
        "query": {
            "model": model_code,
            "condition": config.condition,
            "options": {
                "Year": years,
                "PAINT": [p.value for p in config.paints],
                "TRIM": [t.value for t in config.trims],
            },
            "arrangeby": "Price",
            "order": "asc",
            "market": config.market,
            "language": config.language,
            "super_region": "north america",
            "PaymentType": "cash",
            "Odometer": f"0,{config.max_odometer}",
            "lng": config.longitude,
            "lat": config.latitude,
            "zip": config.zip_code,
            "range": 0,
            "region": config.market,
        },
        "offset": 0,
        "count": 50,
        "outsideOffset": 0,
        "outsideSearch": False,
        "isFalconDeliverySelectionEnabled": False,
        "version": None,
    }


_FETCH_API_JS = """async (apiUrl) => {
    try {
        const resp = await fetch(apiUrl, {
            credentials: 'include',
            headers: { 'Accept': 'application/json' }
        });
        if (!resp.ok) return { error: resp.status };
        return { data: await resp.json() };
    } catch (e) {
        return { error: e.message };
    }
}"""


def _fetch_api_via_page(page: Page, api_url: str) -> dict[str, object]:
    # Tesla sometimes navigates the page (lazy chunk, redirect, popup) right
    # as we run page.evaluate, destroying the JS execution context. Retry
    # once after a short wait — it's a transient race, not a real failure.
    try:
        result: dict[str, object] = page.evaluate(_FETCH_API_JS, api_url)
        return result
    except PlaywrightError as e:
        if "Execution context was destroyed" not in str(e):
            raise
        log.warning("Page navigated during evaluate, retrying after 3s...")
        page.wait_for_timeout(3000)
        retry: dict[str, object] = page.evaluate(_FETCH_API_JS, api_url)
        return retry


class TeslaPlaywrightGateway:
    def __init__(self, config: TeslaSearchConfig) -> None:
        self._config = config
        self._page_url = _build_inventory_url(config)
        self._api_query = _build_api_query(config)

    def fetch_vehicles(self, known: Mapping[str, Vehicle]) -> list[Vehicle]:
        del known  # Tesla API returns everything in one call, no per-id cache needed.
        encoded_query = urllib.parse.quote(json.dumps(self._api_query))
        api_url = (
            f"https://www.tesla.com/inventory/api/v4/inventory-results"
            f"?query={encoded_query}"
        )

        with Camoufox(headless=True) as browser:
            page = browser.new_page()

            log.info(f"Loading Tesla {self._config.model.value} inventory page via Camoufox...")
            page.goto(self._page_url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(10000)

            log.info("Trying Tesla inventory API...")
            raw_result = _fetch_api_via_page(page, api_url)

            if "error" in raw_result:
                raise RuntimeError(f"Tesla API call failed: {raw_result['error']}")

            response = TeslaInventoryResponse.model_validate(raw_result.get("data", {}))
            log.info(f"API returned {len(response.results)} raw result(s).")
            vehicles: list[Vehicle] = []
            for r in response.results:
                v = _to_vehicle(
                    r, self._config.model, self._config.language, self._config.market
                )
                if v is None:
                    continue
                log.info(
                    f"  {r.VIN[-6:]}: AUTOPILOT={r.AUTOPILOT} -> {v.autopilot.value}"
                )
                vehicles.append(v)

        return vehicles
