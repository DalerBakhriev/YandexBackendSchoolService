from datetime import datetime

from dateutil.relativedelta import relativedelta
from starlette.testclient import TestClient

from app.main import app
from app.models.citizen import MAX_STRING_PARAMETER_LENGTH
from tests.utils import import_data_sample, TestConfig

test_conf = TestConfig()
NUM_CITIZENS_IN_SAMPLE = 10


def setup():

    with TestClient(app) as client:
        client.delete(
            "/reset_data",
            json={"admin_login": f"{test_conf.ADMIN_LOGIN}",
                  "admin_password": f"{test_conf.ADMIN_PASSWORD}"}
        )
    test_conf.IMPORT_ID = import_data_sample(num_citizens=NUM_CITIZENS_IN_SAMPLE, with_relatives=True)


def teardown():

    with TestClient(app) as client:
        client.delete(
            "/reset_data",
            json={"admin_login": f"{test_conf.ADMIN_LOGIN}",
                  "admin_password": f"{test_conf.ADMIN_PASSWORD}"}
        )


def test_patch_wrong_date_format():
    """
    Tests case with wrong date during updating citizens.
    Application should return 400 bad request
    :return:
    """
    with TestClient(app) as client:
        patch_wrong_date_response = client.patch(
            f"/imports/{test_conf.IMPORT_ID}/citizens/2",
            json={
                "birth_date": "31.06.2000"
            }
        )
        assert patch_wrong_date_response.status_code == 400


def test_patch_wrong_gender():
    """
    Tests case with wrong gender during updating citizens.
    Application should return 400 bad request
    :return:
    """
    with TestClient(app) as client:
        patch_wrong_gender_response = client.patch(
            f"/imports/{test_conf.IMPORT_ID}/citizens/2",
            json={
                "gender": "something_else"
            }
        )
        assert patch_wrong_gender_response.status_code == 400


def test_patch_empty_data():
    """
    Tests case with empty data during updating citizens.
    Application should return 400 bad request
    :return:
    """

    with TestClient(app) as client:
        patch_empty_data_response = client.patch(
            f"/imports/{test_conf.IMPORT_ID}/citizens/2",
            json={}
        )
        assert patch_empty_data_response.status_code == 400


def test_patch_not_existing_citizen():
    """
    Tests case with updating non existing citizen.
    Application should return 400 bad request
    :return:
    """
    with TestClient(app) as client:
        patch_not_existing_citizen_response = client.patch(
            f"/imports/{test_conf.IMPORT_ID}/citizens/{NUM_CITIZENS_IN_SAMPLE + 2}",
            json={
                "name": "Васек"
            }
        )
        assert patch_not_existing_citizen_response.status_code == 400


def test_patch_not_existing_import():
    """
    Tests case with updating non existing import.
    Application should return 400 bad request
    :return:
    """

    with TestClient(app) as client:
        patch_not_existing_citizen_response = client.patch(
            f"/imports/{test_conf.IMPORT_ID + 1}/citizens/{NUM_CITIZENS_IN_SAMPLE - 2}",
            json={
                "name": "Алешка"
            }
        )
        assert patch_not_existing_citizen_response.status_code == 400


def test_patch_future_birth_date():
    """
    Tests case when birth_date is later then current date
    Application should return 400 bad request
    :return:
    """

    with TestClient(app) as client:
        _curr_date = datetime.utcnow()
        _later_date = _curr_date + relativedelta(days=1)
        later_date = _later_date.strftime("%d.%m.%Y")

        response = client.patch(
            f"/imports/{test_conf.IMPORT_ID}/citizens/{NUM_CITIZENS_IN_SAMPLE - 2}",
            json={
                "birth_date": later_date
            }
        )

        assert response.status_code == 400


def test_patch_negative_apartment_number():
    """
    Tests case when apartment number for updating is negative
    Application should return 400 bad request
    :return:
    """
    with TestClient(app) as client:
        response = client.patch(
            f"/imports/{test_conf.IMPORT_ID}/citizens/{NUM_CITIZENS_IN_SAMPLE - 2}",
            json={
                "apartment": -5
            }
        )

        assert response.status_code == 400


def test_patch_with_extra_field():
    """
    Tests case when extra field is added in patch.
    Application should return 400 bad request
    :return:
    """
    with TestClient(app) as client:
        patch_response = client.patch(
            f"/imports/{test_conf.IMPORT_ID}/citizens/{NUM_CITIZENS_IN_SAMPLE - 2}",
            json={
                "name": "changed_name",
                "extra_field": "patch_for_extra_field"
            }
        )

        assert patch_response.status_code == 400


def test_patch_with_empty_name():
    """
    Tests case when citizen is patched by empty name.
    Application should return 400 bad request
    :return:
    """
    with TestClient(app) as client:
        patch_response = client.patch(
            f"/imports/{test_conf.IMPORT_ID}/citizens/{NUM_CITIZENS_IN_SAMPLE - 2}",
            json={
                "name": ""
            }
        )

        assert patch_response.status_code == 400


def test_patch_with_too_long_string_parameter():
    """
    Tests case when citizen has too long string parameter (town, street, building or name).
    Application should return 400 bad request
    :return:
    """

    for parameter in ("town", "street", "building", "name"):

        with TestClient(app) as client:
            patch_response = client.patch(
                f"/imports/{test_conf.IMPORT_ID}/citizens/{NUM_CITIZENS_IN_SAMPLE - 2}",
                json={
                    parameter: "s" * (MAX_STRING_PARAMETER_LENGTH + 1)
                }
            )

            assert patch_response.status_code == 400


def test_patch_without_any_number_or_letter_in_string_parameter():
    """
    Tests case when citizen has too long string parameter (town, street, building or name).
    Application should return 400 bad request
    :return:
    """

    for parameter in ("town", "street", "building"):

        with TestClient(app) as client:
            patch_response = client.patch(
                f"/imports/{test_conf.IMPORT_ID}/citizens/{NUM_CITIZENS_IN_SAMPLE - 2}",
                json={
                    parameter: "?" * (MAX_STRING_PARAMETER_LENGTH - 200)
                }
            )

            assert patch_response.status_code == 400


def test_patch_with_null_value():
    """
    Tests case when citizen is patched by null value.
    Application should return 400 bad request
    :return:
    """
    with TestClient(app) as client:
        patch_response = client.patch(
            f"/imports/{test_conf.IMPORT_ID}/citizens/{NUM_CITIZENS_IN_SAMPLE - 3}",
            json={
                "name": "some_name",
                "street": None
            }
        )

        assert patch_response.status_code == 400
