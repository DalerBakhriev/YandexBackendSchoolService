from typing import Dict, List, Union

from starlette.testclient import TestClient

from app.main import app
from tests.utils import TestConfig, import_data_sample, calculate_age_percentiles_by_town
from tests.utils import generate_citizens_sample

test_conf = TestConfig()


def setup():

    with TestClient(app) as client:
        client.delete(
            "/reset_data",
            json={"admin_login": f"{test_conf.ADMIN_LOGIN}",
                  "admin_password": f"{test_conf.ADMIN_PASSWORD}"}
        )


def teardown():

    with TestClient(app) as client:
        client.delete(
            "/reset_data",
            json={"admin_login": f"{test_conf.ADMIN_LOGIN}",
                  "admin_password": f"{test_conf.ADMIN_PASSWORD}"}
        )


def test_calculate_for_nonexistent_import_id():
    """
    Tests case with request too nonexistend import id
    Application should return 400 bad request
    :return:
    """
    import_id = import_data_sample(
        num_citizens=10,
        with_relatives=False
    )

    with TestClient(app) as client:
        response_nonexistent_import_id = client.get(
            f"/imports/{import_id + 1}/towns/stat/percentile/age"
        )

        assert response_nonexistent_import_id.status_code == 400


def test_calculate_age_percentiles_by_town():
    """
    Checks if calculations by two different ways return the same result
    :return:
    """
    citizens: List[Dict[str, Union[str, int, List[int]]]] = generate_citizens_sample(
        num_citizens=100,
        with_relatives=False
    )
    with TestClient(app) as client:
        import_response = client.post(
            "/imports",
            json={"citizens": citizens}
        )

        assert import_response.status_code == 201
        assert isinstance(import_response.json()["data"]["import_id"], int)
        import_id = int(import_response.json()["data"]["import_id"])

        age_percentiles_by_town_response = client.get(
            f"/imports/{import_id}/towns/stat/percentile/age"
        ).json()["data"]
        age_percentiles_by_town = calculate_age_percentiles_by_town(citizens_in_import=citizens)

        age_percentiles_sorted_by_town_response = sorted(
            age_percentiles_by_town_response,
            key=lambda stats: stats["town"]
        )
        age_percentiles_sorted_by_town = sorted(
            age_percentiles_by_town,
            key=lambda stats: stats["town"]
        )

        for response_result, calculation_result in zip(
            age_percentiles_sorted_by_town_response, age_percentiles_sorted_by_town
        ):
            assert response_result["town"] == calculation_result["town"]
            assert response_result["p50"] == calculation_result["p50"]
            assert response_result["p75"] == calculation_result["p75"]
            assert response_result["p99"] == calculation_result["p99"]