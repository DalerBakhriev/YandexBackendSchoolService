from starlette.testclient import TestClient

from app.main import app

client = TestClient(app)


def import_data_sample() -> int:
    """
    Imports test data sample
    :return:
    """
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
                 "relatives": [2]},
                {"citizen_id": 2,
                 "town": "Москва",
                 "street": "Льва Толстого",
                 "building": "16к7стр5",
                 "apartment": 7,
                 "name": "Иванов Сергей Иванович",
                 "birth_date": "17.04.1997",
                 "gender": "male",
                 "relatives": [1]}
            ]
        }
    )

    import_id = int(import_response.json()["data"]["import_id"])
    return import_id


def test_import_inconsistent_relatives():
    """
    Tests case with inconsistent relatives list during uploading data
    to database. In this case application should return code 400 bad request
    :return:
    """

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


def test_import_clean_data():
    """
    Tests case with clear data during uploading citizens
    Application should return 201 created
    :return:
    """
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
    assert import_response.status_code == 201


def test_patch_wrong_date_format():
    """
    Tests case with wrong date during updating citizens.
    Application should return 400 bad request
    :return:
    """
    import_id = import_data_sample()
    patch_wrong_date_response = client.patch(
        f"/imports/{import_id}/citizens/2",
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

    import_id = import_data_sample()
    patch_wrong_gender_response = client.patch(
        f"/imports/{import_id}/citizens/2",
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

    import_id = import_data_sample()
    patch_empty_data_response = client.patch(
        f"/imports/{import_id}/citizens/2",
        json={}
    )
    assert patch_empty_data_response.status_code == 400


def test_patch_not_existing_citizen():
    """
    Tests case with empty data during updating citizens.
    Application should return 400 bad request
    :return:
    """

    import_id = import_data_sample()
    patch_not_existing_citizen_response = client.patch(
        f"/imports/{import_id}/citizens/3",
        json={}
    )
    assert patch_not_existing_citizen_response.status_code == 400


def test_clear_database():

    client.post(
        "/clear",
        headers={"token": "980b1f79-4d51-4be5-a0b7-f84b2f91916b"}
    )
