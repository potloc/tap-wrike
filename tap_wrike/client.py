import csv
import backoff
import requests
import singer


API_VERSION = "v4"
API_URL = f"https://www.wrike.com/api/{API_VERSION}"
AUTH_URL = "https://login.wrike.com/oauth2/token"
LOGGER = singer.get_logger()

class Server5xxError(Exception):
    pass

class UnauthorizedError(Exception):
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
    def get(self, path, parse_json=True, **params):
        url = f"{API_URL}/{path}" if "http" not in path else path

        headers = {
            "Authorization": f"Bearer {self.token}"
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code >= 500:
            raise Server5xxError()

        # NOTE: If we notice rate limiting, use the following singer util:
        # https://github.com/singer-io/singer-python/blob/master/singer/utils.py#L81

        if response.status_code == 401 or response.status_code == 403:
            raise UnauthorizedError()

        if response.status_code != 200:
            LOGGER.error(f"{response.status_code}: {response.text}")
            response.raise_for_status()

        data = response
        next_page_token = None # Default value
        if parse_json:
            # Catch invalid json response
            try:
                response_json = response.json()
            except Exception as err:
                LOGGER.error(str(err))
                raise

            data = response_json.get("data")
            next_page_token = response_json.get("nextPageToken")

        return data, next_page_token

class OAuth2Client:
    def __init__(self, client_id, client_secret, refresh_token):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.cached_client = None

    @backoff.on_exception(
        backoff.expo,
        (Server5xxError, ConnectionError),
        max_tries=7,
        factor=3,
    )
    def get_access_token(self):
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "scope": "wsReadOnly,dataExportFull,amReadOnlyGroup"
        }

        response = requests.post(AUTH_URL, headers=headers, data=data)
        if response.status_code >= 500:
            raise Server5xxError()

        if response.status_code != 200:
            LOGGER.error(f"{response.status_code}: {response.text}")
            response.raise_for_status()

        # Catch invalid json response
        try:
            response_json = response.json()
        except Exception as err:
            LOGGER.error(str(err))
            raise

        return response_json["access_token"]

    def refresh_client(self):
        self.cached_client = Client(self.get_access_token())

    def get_client(self):
        if self.cached_client is None:
            self.refresh_client()
        return self.cached_client

    def get(self, path, **params):
        for _attempt in range(10):
            client = self.get_client()
            try:
                return client.get(path, **params)
            except UnauthorizedError:
                self.refresh_client()

# Some Wrike Data can only be obtained through the "dataExport" API.
# This API returns a list of URLs pointing to CSV files
class CSVClient:
    def __init__(self, oauth_client):
        self.client = oauth_client
        self.data_export_cache = None

    def get_data_export_urls(self):
        if self.data_export_cache is None:
            data_export_resources = self.client.get("data_export")[0][0].get("resources", [])
            data_export_map = { resource.get("name"): resource.get("url") for resource in data_export_resources }
            self.data_export_cache = data_export_map
        return self.data_export_cache

    def get(self, table_name, **params):
        csv_url = self.get_data_export_urls().get(table_name)

        if csv_url is None:
            LOGGER.error(f"No CSV URL found for table {table_name}")
            raise

        response, next_page_token = self.client.get(csv_url, parse_json=False)
        # reader = csv.DictReader(response.text.splitlines(), delimiter=",")
        # for item in reader:
        #     LOGGER.info(item)
        return csv.DictReader(response.text.splitlines(), delimiter=","), next_page_token
