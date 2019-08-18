import os
from datetime import datetime

from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from starlette.testclient import TestClient

from app.main import app
from tests.utils import import_data_sample, TestConfig

load_dotenv(os.path.join("..", ".env"))
test_conf = TestConfig()


def setup():
    test_conf.SECRET_TOKEN = os.getenv("SECRET_TOKEN", "")
    with TestClient(app) as client:
        client.post(
            "/clear_db",
            headers={"token": f"{test_conf.SECRET_TOKEN}"}
        )
    test_conf.IMPORT_ID = import_data_sample()


def teardown():
    with TestClient(app) as client:
        client.post(
            "/clear_db",
            headers={"token": f"{test_conf.SECRET_TOKEN}"}
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
            f"/imports/{test_conf.IMPORT_ID}/citizens/3",
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
            f"/imports/{test_conf.IMPORT_ID + 1}/citizens/2",
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
        _curr_date = datetime.now()
        _later_date = _curr_date + relativedelta(days=1)
        later_date = _later_date.strftime("%d.%m.%Y")

        response = client.patch(
            f"/imports/{test_conf.IMPORT_ID}/citizens/2",
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
            f"/imports/{test_conf.IMPORT_ID}/citizens/2",
            json={
                "apartment": -5
            }
        )

        assert response.status_code == 400
