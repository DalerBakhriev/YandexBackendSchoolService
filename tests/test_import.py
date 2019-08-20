import os
from datetime import datetime

from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from starlette.testclient import TestClient

from app.main import app
from tests.utils import TestConfig

load_dotenv(os.path.join("..", ".env"))

test_conf = TestConfig()


def setup():
    test_conf.ADMIN_LOGIN = os.getenv("ADMIN_LOGIN", "")
    test_conf.ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
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


def test_import_inconsistent_relatives():
    """
    Tests case with inconsistent relatives list during uploading data
    to database. In this case application should return code 400 bad request
    :return:
    """
    with TestClient(app) as client:
        response = client.post(
            "/imports",
            json={
                "citizens": [
                    {"citizen_id": 1,
                     "town": "Москва",
                     "street": "Льва Толстого",
                     "building": "16к7стр5",
                     "apartment": 7,
                     "name": "Иванов Иван Иванович",
                     "birth_date": "26.12.1986",
                     "gender": "male",
                     "relatives": [2]},
                    {"citizen_id": 2,
                     "town": "Москва",
                     "street": "Льва Толстого",
                     "building": "16к7стр5",
                     "apartment": 7,
                     "name": "Иванов Сергей Иванович",
                     "birth_date": "17.04.1997",
                     "gender": "male",
                     "relatives": []}
                ]
            }
        )

        assert response.status_code == 400


def test_import_wrong_date_format():
    """
    Tests case with wrong date in during uploading citizens.
    Application should return 400 bad request
    :return:
    """
    with TestClient(app) as client:
        response = client.post(
            "/imports",
            json={
                "citizens": [
                    {"citizen_id": 1,
                     "town": "Москва",
                     "street": "Льва Толстого",
                     "building": "16к7стр5",
                     "apartment": 7,
                     "name": "Иванов Иван Иванович",
                     "birth_date": "30.02.1986",  # wrong data is here
                     "gender": "male",
                     "relatives": []}
                ]}
        )

        assert response.status_code == 400


def test_import_wrong_gender():
    """
    Test case when gender is invalid.
    Gender should be male or female.
    Application should return 400 Bad request
    :return:
    """
    with TestClient(app) as client:
        response = client.post(
            "/imports",
            json={
                "citizens": [
                    {"citizen_id": 1,
                     "town": "Москва",
                     "street": "Льва Толстого",
                     "building": "16к7стр5",
                     "apartment": 7,
                     "name": "Иванов Иван Иванович",
                     "birth_date": "28.02.1986",
                     "gender": "nope",  # invalid gender is here
                     "relatives": []}
                ]}
        )

        assert response.status_code == 400


def test_import_duplicated_citizen_id():
    """
    Tests case when citizen_id is duplicated
    Application should return 400 bad request
    :return:
    """
    with TestClient(app) as client:
        response = client.post(
            "/imports",
            json={
                "citizens": [
                    {"citizen_id": 1,
                     "town": "Москва",
                     "street": "Льва Толстого",
                     "building": "16к7стр5",
                     "apartment": 7,
                     "name": "Иванов Иван Иванович",
                     "birth_date": "28.02.1986",
                     "gender": "male",  # invalid gender is here
                     "relatives": []},
                    {"citizen_id": 1,
                     "town": "Москва",
                     "street": "Большая Ордынка",
                     "building": "11к7стр2",
                     "apartment": 9,
                     "name": "Васильев Василий Васильевич",
                     "birth_date": "23.02.1996",
                     "gender": "female",  # invalid gender is here
                     "relatives": []}
                ]}
        )

        assert response.status_code == 400


def test_future_birth_date_import():
    """
    Tests case when birth_date is later then current date
    Application should return 400 bad request
    :return:
    """
    _curr_date = datetime.now()
    _later_date = _curr_date + relativedelta(days=1)
    later_date = _later_date.strftime("%d.%m.%Y")
    with TestClient(app) as client:
        response = client.post(
            "/imports",
            json={
                "citizens": [
                    {"citizen_id": 1,
                     "town": "Москва",
                     "street": "Льва Толстого",
                     "building": "16к7стр5",
                     "apartment": 7,
                     "name": "Иванов Иван Иванович",
                     "birth_date": later_date,
                     "gender": "nope",  # invalid gender is here
                     "relatives": []}
                ]}
        )

        assert response.status_code == 400


def test_import_negative_apartment_data():
    """
    Tests case with negative apartment data to import
    Application should return 400 bad request
    :return:
    """
    with TestClient(app) as client:
        import_response = client.post(
            "/imports",
            json={
                "citizens": [
                    {"citizen_id": 1,
                     "town": "Москва",
                     "street": "Льва Толстого",
                     "building": "16к7стр5",
                     "apartment": -7,
                     "name": "Иванов Иван Иванович",
                     "birth_date": "26.12.1986",
                     "gender": "male",
                     "relatives": []},
                ]
            }
        )

        assert import_response.status_code == 400


def test_import_clean_data():
    """
    Tests case with clear data during uploading citizens
    Application should return 201 created
    :return:
    """
    with TestClient(app) as client:
        import_response = client.post(
            "/imports",
            json={
                "citizens": [
                    {"citizen_id": 1,
                     "town": "Москва",
                     "street": "Льва Толстого",
                     "building": "16к7стр5",
                     "apartment": 7,
                     "name": "Иванов Иван Иванович",
                     "birth_date": "26.12.1986",
                     "gender": "male",
                     "relatives": []},
                ]
            }
        )
        response_body = import_response.json()
        assert import_response.status_code == 201
        assert "data" in response_body
        assert "import_id" in response_body["data"]
        assert isinstance(response_body["data"]["import_id"], int)


def test_import_swagger_example_is_ok():
    """
    Tests that swagger example for import is ok and works
    Application should return 201 Created
    :return:
    """
    with TestClient(app) as client:
        import_response = client.post(
            "/imports",
            json={"citizens": [
                {
                    "citizen_id": 1,
                    "town": "Москва",
                    "street": "Бассейная",
                    "building": "16к7стр5",
                    "apartment": 666,
                    "name": "Рассеяный",
                    "birth_date": "23.11.2001",
                    "gender": "male",
                    "relatives": []
                }
            ]}
        )
        response_body = import_response.json()
        assert import_response.status_code == 201
        assert "data" in response_body
        assert "import_id" in response_body["data"]
        assert isinstance(response_body["data"]["import_id"], int)


