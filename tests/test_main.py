from starlette.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_inconsistent_relatives():
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


def test_wrong_date_format():
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


def test_wrong_gender():
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

