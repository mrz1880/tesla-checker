from src.infrastructure.tesla_api_schemas import TeslaInventoryResponse


class TestTeslaInventoryResponse:
    def test_parses_results_when_list(self) -> None:
        payload = {
            "total_matches_found": 1,
            "results": [
                {
                    "VIN": "ABC",
                    "TrimName": "Performance",
                    "Year": 2025,
                    "Odometer": 10000,
                    "Price": 50000,
                    "City": "Paris",
                }
            ],
        }

        response = TeslaInventoryResponse.model_validate(payload)

        assert len(response.results) == 1
        assert response.results[0].VIN == "ABC"

    def test_flattens_results_when_dict_with_exact_matches(self) -> None:
        payload = {
            "results": {
                "exact": [{"VIN": "ABC", "Year": 2025}],
                "approximate": [{"VIN": "OTHER"}],
                "approximateOutside": [],
            }
        }

        response = TeslaInventoryResponse.model_validate(payload)

        assert len(response.results) == 1
        assert response.results[0].VIN == "ABC"

    def test_returns_empty_when_dict_with_no_exact_matches(self) -> None:
        # This is the shape Tesla returned on 2026-05-08 that crashed prod.
        payload = {
            "results": {
                "exact": [],
                "approximate": [{"VIN": "NEAR"}],
                "approximateOutside": [],
            }
        }

        response = TeslaInventoryResponse.model_validate(payload)

        assert response.results == []

    def test_handles_missing_results_key(self) -> None:
        response = TeslaInventoryResponse.model_validate({})

        assert response.results == []
