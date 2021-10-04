import backoff
import requests
import singer


API_VERSION = "v4"
API_URL = f"https://www.wrike.com/api/{API_VERSION}"
LOGGER = singer.get_logger()

class Server5xxError(Exception):
    pass

class Client:
    def __init__(self, token):
        self.token = token

    @backoff.on_exception(
        backoff.expo,
        (Server5xxError, ConnectionError),
        max_tries=7,
        factor=3
    )
    def get(self, path, **params):
        url = f"{API_URL}/{path}"

        headers = {
            "Authorization": f"Bearer {self.token}"
        }

        response = requests.get(url, headers=headers, params=params)

        if response.status_code >= 500:
            raise Server5xxError()

        # TODO: Rate limits?

        if response.status_code != 200:
            LOGGER.error(f"{response.status_code}: {response.text}")
            response.raise_for_status()

        # Catch invalid json response
        try:
            response_json = response.json()
        except Exception as err:
            LOGGER.error(str(err))
            raise

        return response_json["data"], response_json.get("nextPageToken")
