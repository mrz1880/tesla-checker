from __future__ import annotations

import json
import logging
import re
import urllib.parse

from camoufox import Camoufox
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page

from src.config import SearchConfig
from src.domain.vehicle import Paint, Trim, Vehicle
from src.infrastructure.tesla_api_schemas import TeslaInventoryResponse, TeslaVehicleResult

log = logging.getLogger(__name__)

_TRIM_MAP: dict[str, Trim] = {t.value: t for t in Trim}
_PAINT_MAP: dict[str, Paint] = {p.value: p for p in Paint}

_TRIM_LABEL_MAP: dict[str, Trim] = {
    "Grande Autonomie, transmission intégrale": Trim.LRAWD,
    "Premium Grande Autonomie Transmission intégrale": Trim.PRAWD,
    "Premium Transmission intégrale": Trim.PRAWD,
    "Performance Transmission Intégrale": Trim.PAWD,
}


def _to_vehicle(r: TeslaVehicleResult) -> Vehicle | None:
    trim_code = r.TRIM[0] if r.TRIM else ""
    paint_code = r.PAINT[0] if r.PAINT else ""

    trim = _TRIM_MAP.get(trim_code)
    paint = _PAINT_MAP.get(paint_code)
    if trim is None or paint is None:
        return None

    return Vehicle(
        vin=r.VIN,
        title=r.TrimName,
        trim=trim,
        year=r.Year,
        odometer=r.Odometer,
        price=r.Price,
        paint=paint,
        has_enhanced_autopilot="ENHANCED_AUTOPILOT" in r.AUTOPILOT,
        city=r.City,
    )


def _scrape_vehicles_from_page(page: Page) -> list[Vehicle]:
    """Fallback: extract vehicle data directly from the rendered page DOM."""
    log.info("Scraping vehicle data from page DOM (fallback)...")

    cards: list[str] = page.evaluate("""() => {
        const results = [];
        document.querySelectorAll('article').forEach(article => {
            const btn = article.querySelector('button');
            if (!btn) return;
            const text = btn.textContent || '';
            results.push(text);
        });
        return results;
    }""")

    vehicles: list[Vehicle] = []
    for card_text in cards:
        vehicle = _parse_card_text(card_text)
        if vehicle is not None:
            vehicles.append(vehicle)

    return vehicles


def _parse_card_text(text: str) -> Vehicle | None:
    """Parse a vehicle card text like:
    'Premium Grande Autonomie Transmission intégrale 40 100 € • Marge
     Véhicule d'occasion certifié de 2024 avec 29 752 km ...'
    """
    trim = None
    title = ""
    for label, trim_val in _TRIM_LABEL_MAP.items():
        if label in text:
            trim = trim_val
            title = label
            break

    if trim is None:
        return None

    price_match = re.search(r"(\d[\d\s]+)\s*€", text)
    year_match = re.search(r"de\s+(20\d{2})\s+avec", text)
    km_match = re.search(r"avec\s+([\d\s]+)\s*km", text)

    if not price_match or not year_match or not km_match:
        return None

    price = int(price_match.group(1).replace(" ", "").replace("\xa0", ""))
    year = int(year_match.group(1))
    odometer = int(km_match.group(1).replace(" ", "").replace("\xa0", ""))

    has_autopilot = "Autopilot amélioré" in text

    paint = Paint.WHITE
    vin = f"DOM-{abs(hash(text)) % 10**10}"

    return Vehicle(
        vin=vin,
        title=title,
        trim=trim,
        year=year,
        odometer=odometer,
        price=price,
        paint=paint,
        has_enhanced_autopilot=has_autopilot,
        city="",
    )


def _build_inventory_url(config: SearchConfig) -> str:
    paints = ",".join(config.paints)
    return (
        f"https://www.tesla.com/{config.language}_{config.market.lower()}"
        f"/inventory/{config.condition}/{config.model}"
        f"?arrangeby=plh&zip={config.zip_code}&range=0"
        f"&PAINT={paints}&AUTOPILOT=ENHANCED_AUTOPILOT"
    )


def _build_api_query(config: SearchConfig) -> dict[str, object]:
    years = list(range(config.min_year, 2027))
    return {
        "query": {
            "model": config.model,
            "condition": config.condition,
            "options": {
                "Year": years,
                "PAINT": list(config.paints),
                "AUTOPILOT": ["ENHANCED_AUTOPILOT"],
                "TRIM": list(config.trims),
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
    def __init__(self, config: SearchConfig) -> None:
        self._config = config
        self._page_url = _build_inventory_url(config)
        self._api_query = _build_api_query(config)

    def fetch_vehicles(self) -> list[Vehicle]:
        encoded_query = urllib.parse.quote(json.dumps(self._api_query))
        api_url = (
            f"https://www.tesla.com/inventory/api/v4/inventory-results"
            f"?query={encoded_query}"
        )

        with Camoufox(headless=True) as browser:
            page = browser.new_page()

            log.info("Loading Tesla inventory page via Camoufox...")
            page.goto(self._page_url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(10000)

            # Strategy 1: call the API directly
            log.info("Trying Tesla inventory API...")
            raw_result = _fetch_api_via_page(page, api_url)

            vehicles: list[Vehicle] = []

            if "error" not in raw_result:
                response = TeslaInventoryResponse.model_validate(raw_result.get("data", {}))
                for result in response.results:
                    vehicle = _to_vehicle(result)
                    if vehicle is not None:
                        vehicles.append(vehicle)
                log.info(f"API returned {len(vehicles)} vehicle(s).")
            else:
                # Strategy 2: scrape from DOM
                log.warning(f"API error ({raw_result['error']}), falling back to DOM scraping.")
                vehicles = _scrape_vehicles_from_page(page)
                log.info(f"DOM scraping returned {len(vehicles)} vehicle(s).")

        return vehicles
