from starlette.testclient import TestClient

from app.main import app


class TestConfig:
    IMPORT_ID = None
    SECRET_TOKEN = None


def import_data_sample() -> int:
    """
    Imports test data sample
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
