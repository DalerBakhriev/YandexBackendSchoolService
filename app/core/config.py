import os

from databases import DatabaseURL

DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
    POSTGRES_USER = os.getenv("POSTGRES_USER", "user")
    POSTGRES_PASS = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_NAME = os.getenv("POSTGRES_DB", "citizens_db")

    DATABASE_URL = DatabaseURL(
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASS}@postgres/{POSTGRES_NAME}"
    )
else:
    DATABASE_URL = DatabaseURL(DATABASE_URL)


MAX_CONNECTIONS_COUNT = int(os.getenv("MAX_CONNECTIONS_COUNT", 10))
MIN_CONNECTIONS_COUNT = int(os.getenv("MIN_CONNECTIONS_COUNT", 7))

# Queries and responses examples for documentation
IMPORT_ENDPOINT_QUERY_BODY_EXAMPLE = {"citizens": [
                {
                    "citizen_id": 1,
                    "town": "Москва",
                    "street": "Бассейная",
                    "building": "дом Колотушкина",
                    "apartment": 666,
                    "name": "Рассеяный",
                    "birth_date": "23.11.2001",
                    "gender": "male",
                    "relatives": []
                }
            ]}

IMPORT_RESPONSE_201_EXAMPLE = {
    "application/json": {
        "data": {
            "import_id": 1
        }
    }
}


PATCH_ENDPOINT_QUERY_BODY_EXAMPLE = {"name": "Рассеяная",
                                     "gender": "female"}

IMPORT_ID_DESCRIPTION = "Import session id"
PATCH_RESPONSE_200_EXAMPLE = {
    "application/json": {
        "example": {
            "citizen_id": 1,
            "town": "Москва",
            "street": "Бассейная",
            "building": "дом Колотушкина",
            "apartment": 666,
            "name": "Рассеяная",
            "birth_date": "23.11.2001",
            "gender": "female",
            "relatives": []
        }
    }
}

GET_CITIZENS_RESPONSE_200_EXAMPLE = {
    "application/json": {
        "data": [
            {
                "citizen_id": 1,
                "town": "Москва",
                "street": "Льва Толстого",
                "building": "16к7стр5",
                "apartment": 7,
                "name": "Иванов Иван Иванович",
                "birth_date": "26.12.1986",
                "gender": "male",
                "relatives": [2, 3]
            },
            {
                "citizen_id": 2,
                "town": "Москва",
                "street": "Льва Толстого",
                "building": "16к7стр5",
                "apartment": 7,
                "name": "Иванов Сергей Иванович",
                "birth_date": "01.04.1997",
                "gender": "male",
                "relatives": [1]
            },
            {
                "citizen_id": 3,
                "town": "Москва",
                "street": "Льва Толстого",
                "building": "16к7стр5",
                "apartment": 7,
                "name": "Иванова Мария Леонидовна",
                "birth_date": "23.11.1986",
                "gender": "female",
                "relatives": [1]
            }
        ]
    }
}

GET_CITIZENS_AND_NUM_PRESENTS_RESPONSE_200_EXAMPLE = {
    "application/json": {
        "data": {
            "1": [],
            "2": [],
            "3": [],
            "4": [{
                "citizen_id": 1,
                "presents": 1,
            }],
            "5": [],
            "6": [],
            "7": [],
            "8": [],
            "9": [],
            "10": [],
            "11": [{
                "citizen_id": 1,
                "presents": 1
            }],
            "12": [{
                "citizen_id": 2,
                "presents": 1},
                {"citizen_id": 3,
                 "presents": 1
                 }]
        }
    }
}

GET_AGE_STATS_BY_TOWN_200_EXAMPLE = {
    "application/json": {
        "data": [
            {
                "town": "Москва",
                "p50": 35.0,
                "p75": 47.5,
                "p99": 59.5
            },
            {
                "town": "Санкт-Петербург",
                "p50": 45.0,
                "p75": 52.5,
                "p99": 97.15
            }
        ]
    }
}

RESET_DATABASE_RESPONSE_200_EXAMPLE = {
    "application/json": {
        "data_was_reset": "ok"
    }
}


