from __future__ import annotations

import json
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

        payload = {
            "topic": self._topic,
            "title": f"Tesla M3 {vehicle.title} ({vehicle.year})",
            "message": (
                f"{vehicle.price:,} EUR | {vehicle.odometer:,} km | {vehicle.color_label}\n"
                f"Lieu: {vehicle.city}\n"
                f"VIN: {vehicle.vin}"
            ),
            "priority": 4,
            "tags": ["car", "zap"],
            "click": vehicle.link,
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self._base_url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    log.info(f"Notification sent for {vehicle.vin}")
                else:
                    log.error(f"Notification failed ({resp.status}) for {vehicle.vin}")
        except Exception as e:
            log.error(f"Notification error: {e}")

    def notify_error(self, message: str) -> None:
        if not self._topic:
            return

        payload = {
            "topic": self._topic,
            "title": "Tesla Checker - Erreur",
            "message": message,
            "priority": 5,
            "tags": ["warning", "rotating_light"],
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self._base_url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    log.info("Error notification sent")
        except Exception as e:
            log.error(f"Failed to send error notification: {e}")
