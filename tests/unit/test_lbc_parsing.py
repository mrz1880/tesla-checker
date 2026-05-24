from src.domain.vehicle import Autopilot, Paint, Trim
from src.infrastructure.lbc_parsing import (
    detect_autopilot,
    detect_paint,
    detect_trim,
    parse_int,
)


class TestDetectAutopilot:
    def test_detects_fsd(self) -> None:
        assert detect_autopilot("Equipée du FSD") == Autopilot.FSD

    def test_detects_full_self_driving(self) -> None:
        assert detect_autopilot("Full Self Driving inclus") == Autopilot.FSD

    def test_detects_capacite_conduite_autonome(self) -> None:
        text = "Capacité de conduite entièrement autonome incluse"
        assert detect_autopilot(text) == Autopilot.FSD

    def test_detects_enhanced_autopilot(self) -> None:
        assert detect_autopilot("Autopilot amélioré présent") == Autopilot.ENHANCED

    def test_detects_pilotage_automatique_ameliore(self) -> None:
        assert detect_autopilot("Pilotage automatique amélioré") == Autopilot.ENHANCED

    def test_detects_with_lbc_typo_ameloire(self) -> None:
        # Real ad we saw on leboncoin had this typo.
        assert detect_autopilot("Pilotage automatique améloiré") == Autopilot.ENHANCED

    def test_fsd_wins_over_eap_when_both_mentioned(self) -> None:
        assert detect_autopilot("FSD et autopilot amélioré") == Autopilot.FSD

    def test_no_autopilot_returns_basic(self) -> None:
        assert detect_autopilot("Berline électrique 4 portes") == Autopilot.BASIC


class TestDetectPaint:
    def test_detects_black(self) -> None:
        assert detect_paint("Peinture noire métallisée") == Paint.BLACK

    def test_detects_white(self) -> None:
        assert detect_paint("Couleur blanc nacré") == Paint.WHITE

    def test_detects_solid_black(self) -> None:
        assert detect_paint("Solid Black") == Paint.BLACK

    def test_returns_other_when_unknown(self) -> None:
        assert detect_paint("Peinture grise stealth") == Paint.OTHER

    def test_returns_other_when_empty(self) -> None:
        assert detect_paint("") == Paint.OTHER


class TestDetectTrim:
    def test_detects_performance(self) -> None:
        text = "TESLA MODEL 3 Performance Dual Motor AWD"
        assert detect_trim(text) == Trim.PAWD

    def test_detects_premium_awd(self) -> None:
        text = "Premium Transmission Intégrale"
        assert detect_trim(text) == Trim.PRAWD

    def test_detects_long_range_awd(self) -> None:
        text = "Model 3 Long Range Dual Motor AWD"
        assert detect_trim(text) == Trim.LRAWD

    def test_detects_grande_autonomie_ti(self) -> None:
        text = "Tesla Model 3 Grande Autonomie transmission intégrale"
        assert detect_trim(text) == Trim.LRAWD

    def test_rejects_when_no_awd_mention(self) -> None:
        text = "Tesla Model 3 Long Range"
        assert detect_trim(text) is None

    def test_rejects_when_only_propulsion(self) -> None:
        text = "Tesla Model 3 Propulsion"
        assert detect_trim(text) is None


class TestParseInt:
    def test_simple(self) -> None:
        assert parse_int("12345") == 12345

    def test_with_spaces(self) -> None:
        assert parse_int("92 500 km") == 92500

    def test_with_unicode_nbsp(self) -> None:
        assert parse_int("40 100 €") == 40100

    def test_empty_returns_none(self) -> None:
        assert parse_int("") is None

    def test_only_letters_returns_none(self) -> None:
        assert parse_int("abc") is None
