from src.domain.vehicle import Paint, SearchCriteria, Trim, Vehicle

CRITERIA = SearchCriteria(
    trims=frozenset({Trim.LRAWD, Trim.PRAWD, Trim.PAWD}),
    paints=frozenset({Paint.WHITE, Paint.BLACK}),
    min_year=2024,
    max_odometer=50000,
    enhanced_autopilot=True,
)


def _make_vehicle(**overrides) -> Vehicle:
    defaults = dict(
        vin="VIN001",
        title="Premium Grande Autonomie TI",
        trim=Trim.PRAWD,
        year=2024,
        odometer=30000,
        price=40000,
        paint=Paint.WHITE,
        has_enhanced_autopilot=True,
        city="Paris",
    )
    defaults.update(overrides)
    return Vehicle(**defaults)


class TestVehicleProperties:
    def test_link(self) -> None:
        vehicle = _make_vehicle(vin="ABC123")
        assert vehicle.link == "https://www.tesla.com/fr_fr/m3/order/ABC123"

    def test_color_label_white(self) -> None:
        assert _make_vehicle(paint=Paint.WHITE).color_label == "Blanc"

    def test_color_label_black(self) -> None:
        assert _make_vehicle(paint=Paint.BLACK).color_label == "Noir"


class TestSearchCriteriaMatching:
    def test_matching_vehicle(self) -> None:
        assert CRITERIA.matches(_make_vehicle())

    def test_rejects_wrong_trim(self) -> None:
        vehicle = _make_vehicle(trim=Trim.LRAWD)
        assert CRITERIA.matches(vehicle)

    def test_rejects_year_too_old(self) -> None:
        assert not CRITERIA.matches(_make_vehicle(year=2023))

    def test_rejects_too_many_km(self) -> None:
        assert not CRITERIA.matches(_make_vehicle(odometer=50001))

    def test_accepts_exact_max_km(self) -> None:
        assert CRITERIA.matches(_make_vehicle(odometer=50000))

    def test_rejects_no_enhanced_autopilot(self) -> None:
        assert not CRITERIA.matches(_make_vehicle(has_enhanced_autopilot=False))

    def test_criteria_without_autopilot_requirement(self) -> None:
        relaxed = SearchCriteria(
            trims=frozenset({Trim.PRAWD}),
            paints=frozenset({Paint.WHITE}),
            min_year=2024,
            max_odometer=50000,
            enhanced_autopilot=False,
        )
        assert relaxed.matches(_make_vehicle(has_enhanced_autopilot=False))

    def test_rejects_wrong_paint(self) -> None:
        criteria = SearchCriteria(
            trims=frozenset({Trim.PRAWD}),
            paints=frozenset({Paint.WHITE}),
            min_year=2024,
            max_odometer=50000,
            enhanced_autopilot=True,
        )
        assert not criteria.matches(_make_vehicle(paint=Paint.BLACK))
