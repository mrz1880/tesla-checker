from src.domain.vehicle import Trim
from src.infrastructure.tesla_playwright_gateway import _parse_card_text


class TestParseCardText:
    def test_parses_prawd_card(self) -> None:
        text = (
            "Premium Grande Autonomie Transmission intégrale 40 100 € • Marge "
            "Véhicule d'occasion certifié de 2024 avec 29 752 km "
            "431 km autonomie (est.) Première immatriculation : 22 sept. 2024 "
            "Couleur 18\" Jantes Intérieur Autopilot amélioré"
        )
        v = _parse_card_text(text)
        assert v is not None
        assert v.trim == Trim.PRAWD
        assert v.year == 2024
        assert v.odometer == 29752
        assert v.price == 40100
        assert v.has_enhanced_autopilot is True

    def test_parses_pawd_card(self) -> None:
        text = (
            "Performance Transmission Intégrale 48 700 € • Marge "
            "Véhicule d'occasion certifié de 2024 avec 25 203 km "
            "autonomie Couleur Jantes Autopilot amélioré"
        )
        v = _parse_card_text(text)
        assert v is not None
        assert v.trim == Trim.PAWD
        assert v.year == 2024
        assert v.odometer == 25203
        assert v.price == 48700

    def test_ignores_propulsion_card(self) -> None:
        text = (
            "Autonomie Standard Plus, Propulsion 22 200 € • Marge "
            "Véhicule d'occasion certifié de 2020 avec 119 472 km"
        )
        v = _parse_card_text(text)
        assert v is None

    def test_ignores_malformed_card(self) -> None:
        assert _parse_card_text("") is None
        assert _parse_card_text("random text") is None

    def test_parses_card_without_autopilot(self) -> None:
        text = (
            "Performance Transmission Intégrale 52 700 € • TVA "
            "Véhicule d'occasion certifié de 2025 avec 10 476 km "
            "autonomie Couleur Jantes"
        )
        v = _parse_card_text(text)
        assert v is not None
        assert v.has_enhanced_autopilot is False
        assert v.year == 2025
        assert v.odometer == 10476
