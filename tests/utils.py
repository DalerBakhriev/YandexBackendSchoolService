import datetime
import os
import random
from collections import defaultdict
from copy import deepcopy
from typing import Dict, List, Union

import numpy as np
from dateutil.relativedelta import relativedelta
from starlette.testclient import TestClient

from app.main import app

CITIZEN_EXAMPLE = {
    "citizen_id": 1,
    "town": "Керчь",
    "street": "Иосифа Бродского",
    "building": "16к7стр5",
    "apartment": 7,
    "name": "Иванов Иван Иванович",
    "birth_date": "01.02.2000",
    "gender": "male",
    "relatives": []
}

TOWNS = (
    "Saint-Petersburg", "Moscow", "London",
    "Paris", "New-York", "Kiev",
    "Stockholm", "Helsinki", "Oslo",
    "Minsk", "Tokyo", "Lisbon", "Amsterdam"
)


class TestConfig:

    IMPORT_ID = None
    ADMIN_LOGIN = os.getenv("ADMIN_LOGIN", "")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")


def import_data_sample(num_citizens: int, with_relatives: bool) -> int:
    """
    Imports test data sample
    :return: import id of uploaded data sample
    """
    citizens: List[Dict[str, Union[str, int, List[int]]]] = generate_citizens_sample(
        num_citizens=num_citizens,
        with_relatives=with_relatives
    )

    with TestClient(app) as client:
        import_response = client.post(
            "/imports",
            json={"citizens": citizens}
        )

        assert import_response.status_code == 201
        assert isinstance(import_response.json()["data"]["import_id"], int)
        import_id = int(import_response.json()["data"]["import_id"])

        return import_id


def generate_birth_dates_sequence(start_date: str) -> List[str]:
    """
    Generates list of dates in string format to choose from.
    Will be used for sampling citizens
    :return:
    """
    start_date = datetime.datetime.strptime(start_date, "%d.%m.%Y")
    end_date = datetime.datetime.utcnow() - datetime.timedelta(days=1)
    dates_seq = [(start_date + datetime.timedelta(days=num_days)).strftime("%d.%m.%Y")
                 for num_days in range((end_date - start_date).days)]

    return dates_seq


def generate_citizens_sample(
        num_citizens: int,
        with_relatives: bool
) -> List[Dict[str, Union[str, int, List[int]]]]:
    """
    Generates sample of citizens with specified size
    :param num_citizens: size of sample
    :param with_relatives: generate relatives or not
    :return: sample of generated citizens
    """

    citizens_sample: List[Dict[str, Union[str, int, List[int]]]] = list()
    birth_dates_seq = generate_birth_dates_sequence(start_date="01.01.1917")

    for citizen_id in range(num_citizens):
        one_more_citizen = deepcopy(CITIZEN_EXAMPLE)
        one_more_citizen["citizen_id"] = citizen_id
        one_more_citizen["town"] = random.choice(TOWNS)
        one_more_citizen["gender"] = random.choice(("male", "female"))
        one_more_citizen["birth_date"] = random.choice(birth_dates_seq)
        citizens_sample.append(one_more_citizen)

    all_possible_relatives = list(range(num_citizens))
    if with_relatives:
        for citizen_id, citizen in enumerate(citizens_sample):
            relatives = all_possible_relatives[:citizen_id] + all_possible_relatives[citizen_id + 1:]
            for relative_id in relatives:
                if citizen_id not in citizens_sample[relative_id]["relatives"]:
                    citizens_sample[relative_id]["relatives"].append(citizen_id)

    return citizens_sample


def calculate_num_birthdays_for_citizens_per_month(
        citizens_in_import: List[Dict[str, Union[str, int, List[int]]]]
) -> Dict[str, List[Dict[int, int]]]:

    """
    Calculates num birthdays for citizen per month
    :param citizens_in_import: citizens in import session
    :return:
    """

    num_birthdays_for_citizens_per_month = defaultdict(list)

    for citizen in citizens_in_import:

        citizen_presents_by_month: Dict[str, int] = {}
        for relative_id in citizen["relatives"]:
            month = str(datetime.datetime.strptime(citizens_in_import[relative_id]["birth_date"], "%d.%m.%Y").month)
            citizen_presents_by_month[month] = citizen_presents_by_month.get(month, 0) + 1

        for month in citizen_presents_by_month:
            num_birthdays_for_citizens_per_month[month].append(
                {"citizen_id": citizen["citizen_id"],
                 "presents": citizen_presents_by_month[month]}
            )

    for month in map(str, range(1, 12 + 1)):
        if month not in num_birthdays_for_citizens_per_month:
            num_birthdays_for_citizens_per_month[month] = []

    return dict(num_birthdays_for_citizens_per_month)


def calculate_age_percentiles_by_town(
        citizens_in_import: List[Dict[str, Union[str, int, List[int]]]]
) -> List[Dict[str, Union[float, str]]]:
    """
    Calculates ages percentile by town
    :param citizens_in_import: citizens in import session
    :return:
    """
    ages_by_town = defaultdict(list)

    for citizen in citizens_in_import:
        age = relativedelta(
            datetime.datetime.utcnow(),
            datetime.datetime.strptime(citizen["birth_date"], "%d.%m.%Y")
        ).years
        ages_by_town[citizen["town"]].append(age)

    ages_percentiles_by_town: List[Dict[str, Union[float, str]]] = list()
    ages_by_town = dict(ages_by_town)

    for town in ages_by_town:

        town_stats: Dict[str, Union[float, str]] = dict()
        town_stats["town"] = town
        town_stats["p50"] = round(np.percentile(ages_by_town[town], q=50, interpolation="linear"), 2)
        town_stats["p75"] = round(np.percentile(ages_by_town[town], q=75, interpolation="linear"), 2)
        town_stats["p99"] = round(np.percentile(ages_by_town[town], q=99, interpolation="linear"), 2)
        ages_percentiles_by_town.append(town_stats)

    return ages_percentiles_by_town


