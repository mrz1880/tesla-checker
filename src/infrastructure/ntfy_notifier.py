from __future__ import annotations

import logging
import urllib.request

from src.domain.vehicle import Vehicle

log = logging.getLogger(__name__)


class NtfyNotifier:
    def __init__(self, topic: str, base_url: str = "https://ntfy.sh") -> None:
        self._topic = topic
        self._base_url = base_url.rstrip("/")

    def notify_new_vehicle(self, vehicle: Vehicle) -> None:
        if not self._topic:
            log.warning("NTFY_TOPIC not set, skipping notification.")
            return

        title = f"Tesla M3 {vehicle.title} ({vehicle.year})"
        body = (
            f"{vehicle.price:,} EUR | {vehicle.odometer:,} km | {vehicle.color_label}\n"
            f"Lieu: {vehicle.city}\n"
            f"VIN: {vehicle.vin}"
        )

        url = f"{self._base_url}/{self._topic}"
        data = body.encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Title", title)
        req.add_header("Priority", "high")
        req.add_header("Tags", "car,zap")
        req.add_header("Click", vehicle.link)

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    log.info(f"Notification sent for {vehicle.vin}")
                else:
                    log.error(f"Notification failed ({resp.status}) for {vehicle.vin}")
        except Exception as e:
            log.error(f"Notification error: {e}")
