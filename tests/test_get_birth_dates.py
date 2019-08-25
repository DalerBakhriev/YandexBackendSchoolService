from typing import Dict, List, Union

from starlette.testclient import TestClient

from app.main import app
from tests.utils import (
    TestConfig,
    import_data_sample,
    calculate_num_birthdays_for_citizens_per_month,
    generate_citizens_sample
)

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


def test_calculate_num_presents_without_any_relatives():
    """
    Tests case when there are no any relatives within specified import id.
    Application should return json with all months and empty list for each of them.
    :return:
    """
    import_id = import_data_sample(
        num_citizens=10,
        with_relatives=False
    )

    with TestClient(app) as client:
        response_for_sample_without_relatives = client.get(
            f"/imports/{import_id}/citizens/birthdays"
        )
        assert response_for_sample_without_relatives.status_code == 200


def test_calculate_num_presents_per_month():
    """
    Checks if calculations by two different ways return the same result
    :return:
    """

    citizens: List[Dict[str, Union[str, int, List[int]]]] = generate_citizens_sample(
        num_citizens=100,
        with_relatives=True
    )
    with TestClient(app) as client:
        import_response = client.post(
            "/imports",
            json={"citizens": citizens}
        )

        assert import_response.status_code == 201
        assert isinstance(import_response.json()["data"]["import_id"], int)
        import_id = int(import_response.json()["data"]["import_id"])
        num_birthdays_response = client.get(
            f"/imports/{import_id}/citizens/birthdays"
        )

        num_birthdays = calculate_num_birthdays_for_citizens_per_month(citizens_in_import=citizens)
        birthdays_data = num_birthdays_response.json()["data"]

        for month in map(str, range(1, 12 + 1)):
            assert birthdays_data[month] == num_birthdays[month]
