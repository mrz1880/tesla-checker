from __future__ import annotations

import logging

from playwright.sync_api import sync_playwright

from src.domain.vehicle import Paint, Trim, Vehicle

log = logging.getLogger(__name__)

TESLA_INVENTORY_URL = (
    "https://www.tesla.com/fr_fr/inventory/used/m3"
    "?arrangeby=plh&zip=59130&range=0"
    "&PAINT=WHITE,BLACK&AUTOPILOT=ENHANCED_AUTOPILOT"
)

_TRIM_MAP: dict[str, Trim] = {t.value: t for t in Trim}
_PAINT_MAP: dict[str, Paint] = {p.value: p for p in Paint}


def _parse_vehicle(raw: dict) -> Vehicle | None:
    trim_code = (raw.get("TRIM") or [""])[0]
    paint_code = (raw.get("PAINT") or [""])[0]

    trim = _TRIM_MAP.get(trim_code)
    paint = _PAINT_MAP.get(paint_code)
    if trim is None or paint is None:
        return None

    autopilot_options = raw.get("AUTOPILOT") or []

    return Vehicle(
        vin=raw.get("VIN", ""),
        title=raw.get("TrimName", ""),
        trim=trim,
        year=raw.get("Year", 0),
        odometer=raw.get("Odometer", 0),
        price=raw.get("Price", 0),
        paint=paint,
        has_enhanced_autopilot="ENHANCED_AUTOPILOT" in autopilot_options,
        city=raw.get("City", ""),
    )


class TeslaPlaywrightGateway:
    def fetch_vehicles(self) -> list[Vehicle]:
        api_data: dict | None = None

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                locale="fr-FR",
                viewport={"width": 1728, "height": 1117},
            )
            page = context.new_page()

            def on_response(response):
                nonlocal api_data
                if "inventory/api/v4/inventory-results" in response.url:
                    try:
                        api_data = response.json()
                    except Exception:
                        pass

            page.on("response", on_response)
            log.info("Navigating to Tesla inventory page...")
            page.goto(TESLA_INVENTORY_URL, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(5000)
            browser.close()

        if api_data is None:
            log.error("No API response intercepted from Tesla.")
            return []

        raw_results = api_data.get("results") or []
        vehicles: list[Vehicle] = []
        for raw in raw_results:
            vehicle = _parse_vehicle(raw)
            if vehicle is not None:
                vehicles.append(vehicle)

        return vehicles
