from __future__ import annotations

import json
import logging
import urllib.request

from src.domain.vehicle import Vehicle

log = logging.getLogger(__name__)


def _vehicle_message(vehicle: Vehicle) -> str:
    return (
        f"{vehicle.price:,} EUR | {vehicle.odometer:,} km"
        f" | {vehicle.color_label} | {vehicle.autopilot_label}\n"
        f"Lieu: {vehicle.city}\n"
        f"Ref: {vehicle.id}"
    )


def _vehicle_title(vehicle: Vehicle, prefix: str) -> str:
    return (
        f"{prefix} {vehicle.source_label} {vehicle.model_label} "
        f"{vehicle.title} ({vehicle.year})"
    ).strip()


class NtfyNotifier:
    def __init__(self, topic: str, base_url: str = "https://ntfy.sh") -> None:
        self._topic = topic
        self._base_url = base_url.rstrip("/")

    def notify_new_vehicle(self, vehicle: Vehicle) -> None:
        self._send(
            title=_vehicle_title(vehicle, prefix=""),
            message=_vehicle_message(vehicle),
            priority=4,
            tags=["car", "zap"],
            click=vehicle.link,
        )

    def notify_sold_vehicle(self, vehicle: Vehicle) -> None:
        self._send(
            title=_vehicle_title(vehicle, prefix="Vendu:"),
            message=_vehicle_message(vehicle),
            priority=2,
            tags=["white_check_mark"],
        )

    def notify_error(self, message: str) -> None:
        self._send(
            title="Tesla Checker - Erreur",
            message=message,
            priority=5,
            tags=["warning", "rotating_light"],
        )

    def _send(
        self,
        title: str,
        message: str,
        priority: int,
        tags: list[str],
        click: str | None = None,
    ) -> None:
        if not self._topic:
            log.warning("NTFY_TOPIC not set, skipping notification.")
            return

        payload: dict[str, object] = {
            "topic": self._topic,
            "title": title,
            "message": message,
            "priority": priority,
            "tags": tags,
        }
        if click is not None:
            payload["click"] = click

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self._base_url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    log.info(f"Notification sent: {title}")
                else:
                    log.error(f"Notification failed ({resp.status}): {title}")
        except Exception as e:
            log.error(f"Notification error: {e}")
