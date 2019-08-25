from copy import deepcopy
from datetime import datetime

from dateutil.relativedelta import relativedelta
from starlette.testclient import TestClient

from app.core.config import IMPORT_ENDPOINT_QUERY_BODY_EXAMPLE
from app.main import app
from app.models.citizen import MAX_STRING_PARAMETER_LENGTH
from tests.utils import TestConfig, CITIZEN_EXAMPLE

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

    citizen_with_wrong_birth_date = deepcopy(CITIZEN_EXAMPLE)
    citizen_with_wrong_birth_date["birth_date"] = "30.02.1986"
    with TestClient(app) as client:
        response = client.post(
            "/imports",
            json={
                "citizens": [citizen_with_wrong_birth_date]}
        )

        assert response.status_code == 400


def test_import_wrong_gender():
    """
    Test case when gender is invalid.
    Gender should be male or female.
    Application should return 400 Bad request
    :return:
    """

    citizen_with_wrong_gender = deepcopy(CITIZEN_EXAMPLE)
    citizen_with_wrong_gender["gender"] = "nope"
    with TestClient(app) as client:
        response = client.post(
            "/imports",
            json={
                "citizens": [citizen_with_wrong_gender]}
        )

        assert response.status_code == 400


def test_import_duplicated_citizen_id():
    """
    Tests case when citizen_id is duplicated
    Application should return 400 bad request
    :return:
    """

    duplicated_citizen = deepcopy(CITIZEN_EXAMPLE)
    with TestClient(app) as client:
        response = client.post(
            "/imports",
            json={
                "citizens": [duplicated_citizen, duplicated_citizen]
            }
        )

        assert response.status_code == 400


def test_future_birth_date_import():
    """
    Tests case when birth_date is later then current date
    Application should return 400 bad request
    :return:
    """
    _curr_date = datetime.utcnow()
    _later_date = _curr_date + relativedelta(days=1)
    later_date = _later_date.strftime("%d.%m.%Y")

    citizen_with_birth_date_later_than_current = deepcopy(CITIZEN_EXAMPLE)
    citizen_with_birth_date_later_than_current["birth_date"] = later_date
    with TestClient(app) as client:
        response = client.post(
            "/imports",
            json={
                "citizens": [
                    citizen_with_birth_date_later_than_current
                ]}
        )

        assert response.status_code == 400


def test_import_negative_apartment_data():
    """
    Tests case with negative apartment data to import
    Application should return 400 bad request
    :return:
    """
    citizen_with_negative_apartment_number = deepcopy(IMPORT_ENDPOINT_QUERY_BODY_EXAMPLE)
    citizen_with_negative_apartment_number["apartment"] = -7
    with TestClient(app) as client:
        import_response = client.post(
            "/imports",
            json={
                "citizens": [
                    citizen_with_negative_apartment_number
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
    citizen_ok = deepcopy(CITIZEN_EXAMPLE)
    with TestClient(app) as client:
        import_response = client.post(
            "/imports",
            json={
                "citizens": [citizen_ok]
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
            json=IMPORT_ENDPOINT_QUERY_BODY_EXAMPLE
        )
        response_body = import_response.json()
        assert import_response.status_code == 201
        assert "data" in response_body
        assert "import_id" in response_body["data"]
        assert isinstance(response_body["data"]["import_id"], int)


def test_import_with_extra_field():
    """
    Tests case when extra field is added in import.
    Application should return 400 bad request
    :return:
    """
    citizen_with_extra_field = deepcopy(CITIZEN_EXAMPLE)
    citizen_with_extra_field["extra_field"] = "this_is_extra_field"
    with TestClient(app) as client:
        import_response = client.post(
            "/imports",
            json={
                "citizens": [citizen_with_extra_field]
            }
        )

        assert import_response.status_code == 400


def test_import_with_empty_name():
    """
    Tests case when citizen has empty name.
    Application should return 400 bad request
    :return:
    """
    citizen_with_empty_name = deepcopy(CITIZEN_EXAMPLE)
    citizen_with_empty_name["name"] = ""
    with TestClient(app) as client:
        import_response = client.post(
            "/imports",
            json={
                "citizens": [citizen_with_empty_name]
            }
        )

        assert import_response.status_code == 400


def test_import_with_too_long_string_parameter():
    """
    Tests case when citizen has too long string parameter (town, street, building or name).
    Application should return 400 bad request
    :return:
    """

    for parameter in ("town", "street", "building", "name"):
        citizen_with_too_long_string_parameter = deepcopy(CITIZEN_EXAMPLE)
        citizen_with_too_long_string_parameter[parameter] = "s" * (MAX_STRING_PARAMETER_LENGTH + 1)
        with TestClient(app) as client:
            import_response = client.post(
                "/imports",
                json={
                    "citizens": [citizen_with_too_long_string_parameter]
                }
            )

            assert import_response.status_code == 400


def test_import_without_any_number_or_letter_in_string_parameter():
    """
    Tests case when citizen has too long string parameter (town, street, building or name).
    Application should return 400 bad request
    :return:
    """

    for parameter in ("town", "street", "building"):
        citizen_without_any_number_or_letter = deepcopy(CITIZEN_EXAMPLE)
        citizen_without_any_number_or_letter[parameter] = "?" * (MAX_STRING_PARAMETER_LENGTH - 200)
        with TestClient(app) as client:
            import_response = client.post(
                "/imports",
                json={
                    "citizens": [citizen_without_any_number_or_letter]
                }
            )

            assert import_response.status_code == 400

