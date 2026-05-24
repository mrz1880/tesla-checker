from typing import Any

from src.domain.search_criteria import SearchCriteria
from src.domain.vehicle import Autopilot, Model, Paint, Source, Trim, Vehicle

CRITERIA = SearchCriteria(
    trims=frozenset({Trim.LRAWD, Trim.PRAWD, Trim.PAWD}),
    paints=frozenset({Paint.WHITE, Paint.BLACK}),
    min_year=2024,
    max_odometer=50000,
    accepted_autopilots=frozenset({Autopilot.ENHANCED}),
)


def _make_vehicle(**overrides: Any) -> Vehicle:
    defaults: dict[str, Any] = dict(
        id="VIN001",
        source=Source.TESLA,
        model=Model.M3,
        title="Premium Grande Autonomie TI",
        trim=Trim.PRAWD,
        year=2024,
        odometer=30000,
        price=40000,
        paint=Paint.WHITE,
        autopilot=Autopilot.ENHANCED,
        city="Paris",
        link="https://www.tesla.com/fr_fr/m3/order/VIN001",
    )
    defaults.update(overrides)
    return Vehicle(**defaults)


class TestVehicleIdentity:
    def test_same_id_same_source_are_equal(self) -> None:
        v1 = _make_vehicle(id="ABC", price=30000)
        v2 = _make_vehicle(id="ABC", price=40000)
        assert v1 == v2

    def test_different_id_are_not_equal(self) -> None:
        v1 = _make_vehicle(id="ABC")
        v2 = _make_vehicle(id="DEF")
        assert v1 != v2

    def test_same_id_different_source_are_not_equal(self) -> None:
        v1 = _make_vehicle(id="ABC", source=Source.TESLA)
        v2 = _make_vehicle(id="ABC", source=Source.LEBONCOIN)
        assert v1 != v2

    def test_same_id_same_hash(self) -> None:
        v1 = _make_vehicle(id="ABC", price=30000)
        v2 = _make_vehicle(id="ABC", price=40000)
        assert hash(v1) == hash(v2)

    def test_can_be_used_in_set(self) -> None:
        v1 = _make_vehicle(id="ABC", price=30000)
        v2 = _make_vehicle(id="ABC", price=40000)
        assert len({v1, v2}) == 1


class TestVehicleProperties:
    def test_link_is_stored(self) -> None:
        vehicle = _make_vehicle(link="https://example.com/foo")
        assert vehicle.link == "https://example.com/foo"

    def test_color_label_white(self) -> None:
        assert _make_vehicle(paint=Paint.WHITE).color_label == "Blanc"

    def test_color_label_black(self) -> None:
        assert _make_vehicle(paint=Paint.BLACK).color_label == "Noir"

    def test_source_label_tesla(self) -> None:
        assert _make_vehicle(source=Source.TESLA).source_label == "Tesla"

    def test_source_label_lbc(self) -> None:
        assert _make_vehicle(source=Source.LEBONCOIN).source_label == "LBC"

    def test_model_label_m3(self) -> None:
        assert _make_vehicle(model=Model.M3).model_label == "M3"

    def test_model_label_my(self) -> None:
        assert _make_vehicle(model=Model.MY).model_label == "MY"


class TestSearchCriteriaMatching:
    def test_matching_vehicle(self) -> None:
        assert CRITERIA.matches(_make_vehicle())

    def test_accepts_other_awd_trim(self) -> None:
        assert CRITERIA.matches(_make_vehicle(trim=Trim.LRAWD))

    def test_rejects_year_too_old(self) -> None:
        assert not CRITERIA.matches(_make_vehicle(year=2023))

    def test_rejects_too_many_km(self) -> None:
        assert not CRITERIA.matches(_make_vehicle(odometer=50001))

    def test_accepts_exact_max_km(self) -> None:
        assert CRITERIA.matches(_make_vehicle(odometer=50000))

    def test_rejects_basic_autopilot_when_enhanced_required(self) -> None:
        assert not CRITERIA.matches(_make_vehicle(autopilot=Autopilot.BASIC))

    def test_rejects_fsd_when_only_enhanced_accepted(self) -> None:
        assert not CRITERIA.matches(_make_vehicle(autopilot=Autopilot.FSD))

    def test_criteria_accepting_fsd_or_enhanced(self) -> None:
        criteria = SearchCriteria(
            trims=frozenset({Trim.PRAWD}),
            paints=frozenset({Paint.WHITE}),
            min_year=2024,
            max_odometer=80000,
            accepted_autopilots=frozenset({Autopilot.ENHANCED, Autopilot.FSD}),
        )
        assert criteria.matches(_make_vehicle(autopilot=Autopilot.FSD))
        assert criteria.matches(_make_vehicle(autopilot=Autopilot.ENHANCED))
        assert not criteria.matches(_make_vehicle(autopilot=Autopilot.BASIC))

    def test_rejects_wrong_paint(self) -> None:
        criteria = SearchCriteria(
            trims=frozenset({Trim.PRAWD}),
            paints=frozenset({Paint.WHITE}),
            min_year=2024,
            max_odometer=50000,
            accepted_autopilots=frozenset({Autopilot.ENHANCED}),
        )
        assert not criteria.matches(_make_vehicle(paint=Paint.BLACK))
        assert not criteria.matches(_make_vehicle(paint=Paint.OTHER))
