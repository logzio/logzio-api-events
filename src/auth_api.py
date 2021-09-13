import logging
import urllib.parse
import requests
import json

from typing import Generator, Optional
from abc import abstractmethod
from datetime import datetime, timedelta
from jsonpath_ng import parse
from dateutil import parser
from .api import Api
from .data.api_credentials import ApiCredentials
from .data.api_filter import ApiFilter
from .data.api_json_paths import ApiJsonPaths


logger = logging.getLogger(__name__)


class AuthApi(Api):

    def __init__(self, api_name: str, api_credentials: ApiCredentials, api_filters: list[ApiFilter],
                 api_url: str = None, api_start_date_name: str = None, api_json_paths: ApiJsonPaths = None):
        self._name = api_name
        self._credentials = api_credentials
        self._start_date_name = api_start_date_name
        self._filters = api_filters
        self._url = api_url
        self._json_paths = api_json_paths
        self._current_data_last_date: Optional[str] = None

    def fetch_data(self) -> Generator:
        total_events, total_events_num = self._get_total_data_from_api()

        if not total_events:
            logger.info("No new events available for api {}.".format(self._name))
            return total_events

        logger.info("Successfully got {0} total events from api {1}.".format(total_events_num, self._name))

        for event in total_events:
            yield json.dumps(event)

        try:
            self._current_data_last_date = self._get_last_date_in_data(total_events)
        except Exception:
            raise

    def update_start_date_filter(self) -> None:
        new_start_date = self._get_new_start_date()

        for api_filter in self._filters:
            if api_filter.key != self._start_date_name:
                continue

            api_filter.value = new_start_date
            return

        self._filters.append(ApiFilter(self._start_date_name, new_start_date))

    def get_last_start_date(self) -> Optional[str]:
        for api_filter in self._filters:
            if api_filter.key != self._start_date_name:
                continue

            return api_filter.value

        return None

    def get_api_name(self):
        return self._name

    def _get_total_data_from_api(self) -> tuple[list, int]:
        total_events = []
        total_events_num = 0
        api_url = self._build_api_url()

        while True:
            try:
                next_url, events, events_num = self._get_data_from_api(api_url)
            except Exception:
                raise

            total_events.extend(events)
            total_events_num += events_num

            if next_url is None or total_events_num >= 2500:
                break

            api_url = next_url

        return total_events, total_events_num

    def _build_api_url(self) -> str:
        api_url = self._url
        api_filters_num = len(self._filters)

        for api_filter in self._filters:
            api_url += api_filter.key + '=' + str(api_filter.value)
            api_filters_num -= 1

            if api_filters_num > 0:
                api_url += '&'

        return api_url

    def _get_data_from_api(self, url: str) -> tuple[str, list, int]:
        try:
            response = self._get_response_from_api(url)
        except Exception:
            raise

        json_data = json.loads(response.content)
        next_url = self._get_json_path_value_from_data(self._json_paths.next_url, json_data)
        events = self._get_json_path_value_from_data(self._json_paths.data, json_data)

        if events is None:
            logger.error(
                "The json path for api {}'s data is wrong. Please change your configuration.".format(self._name))
            raise Api.ApiError

        events_num = len(events)

        logger.info("Successfully got {0} events from api {1}.".format(events_num, self._name))

        return next_url, events, events_num

    def _get_response_from_api(self, url: str):
        try:
            response = requests.get(url=url, auth=(self._credentials.id, self._credentials.key))
            response.raise_for_status()
        except requests.HTTPError as e:
            logger.error(
                "Something went wrong while trying to get the events from api {0}. response: {1}".format(self._name, e))

            if e.response.status_code == 400 or e.response.status_code == 401:
                raise Api.ApiError()

            raise
        except Exception as e:
            logger.error("Something went wrong with api {0}. response: {1}".format(self._name, e))
            raise

        return response

    def _get_last_date_in_data(self, data: list[dict]):
        last_date: Optional[datetime] = None

        for event in data:
            event_date = self._get_json_path_value_from_data(self._json_paths.data_date, event)

            if event_date is None:
                logger.error(
                    "The json path for api {}'s data date is wrong. Please change your configuration.".format(
                        self._name))
                raise Api.ApiError

            event_date_datetime = parser.parse(event_date)

            if last_date is None:
                last_date = event_date_datetime
                continue

            if last_date < event_date_datetime:
                last_date = event_date_datetime

        return str(last_date)

    def _get_json_path_value_from_data(self, json_path: str, data: dict):
        match = parse(json_path).find(data)

        if not match:
            return None

        return match[0].value

    def _get_new_start_date(self) -> str:
        new_start_date = str(parser.parse(self._current_data_last_date) + timedelta(seconds=1))
        new_start_date = new_start_date.replace(' ', 'T')
        new_start_date = urllib.parse.quote(new_start_date)

        return new_start_date
