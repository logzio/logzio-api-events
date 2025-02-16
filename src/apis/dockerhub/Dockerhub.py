import time
from datetime import datetime, timedelta, UTC
import json
import logging
import requests
from pydantic import Field
from src.apis.general.Api import ApiFetcher

logger = logging.getLogger(__name__)


class DockerHub(ApiFetcher):
    """
    :param dockerhub_user: The DockerHub username
    :param dockerhub_token: The DockerHub personal access token or password
    :param days_back_fetch: Number of days to fetch back in the first request, Optional (adds a filter on 'from')
    :param page_size: Number of events to return in a single request (for pagination)
    :param refresh_token_interval: Interval in minutes to refresh the JWT token
    """
    dockerhub_user: str = Field(frozen=True)
    dockerhub_token: str = Field(frozen=False)
    days_back_fetch: int = Field(default=-1, frozen=True)
    refresh_token_interval: int = Field(default=30)
    _jwt_token: str = None
    _token_expiry: datetime = None

    def __init__(self, **data):
        res_data_path = "logs"
        headers = {
            "Content-Type": "application/json",
        }
        super().__init__(headers=headers, response_data_path=res_data_path, **data)
        self._initialize_params()

    def _initialize_params(self):
        try:
            params = {"page_size": 100}
            if self.days_back_fetch > 0:
                from_date = (datetime.now(UTC) - timedelta(days=self.days_back_fetch)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                params["from"] = from_date
            query_string = "&".join([f"{key}={value}" for key, value in params.items()])
            if "?" in self.url:
                self.url += f"&{query_string}"
            else:
                self.url += f"?{query_string}"
        except Exception as e:
            logger.error(
                f"Failed to update request params. Sending {self.name} request with default params. Error: {e}")

    def _get_jwt_token(self):
        if self._jwt_token and datetime.now(UTC) < self._token_expiry:
            return self._jwt_token

        url = "https://hub.docker.com/v2/users/login"
        payload = {
            "username": self.dockerhub_user,
            "password": self.dockerhub_token
        }
        headers = {"Content-Type": "application/json"}
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            token_response = response.json()
            self._jwt_token = token_response.get("token")
            self._token_expiry = datetime.now(UTC) + timedelta(minutes=self.refresh_token_interval)
            return self._jwt_token
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get JWT token: {e}")

    def send_request(self):
        session_token = self._get_jwt_token()
        self.headers["Authorization"] = f"Bearer {session_token}"
        response = super().send_request()
        return response
