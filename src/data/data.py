import urllib
from datetime import datetime
from enum import Enum

import jsonschema
import requests

ALPACA_BTC_SCHEMA = {
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "t": {"type": "string", "format": "date-time"},
      "o": {"type": "number"},
      "h": {"type": "number"},
      "l": {"type": "number"},
      "c": {"type": "number"},
      "v": {"type": "number"},
    },
    "required": ["t", "o", "h", "l", "c", "v"],
  },
}


def validateInstance(data, schema=ALPACA_BTC_SCHEMA):
  """Validate data against a given JSON schema.
  :param data: data to be validated
  :param schema: JSON schema to validate against
  :type data: any
  :type schema: dict
  :raises jsonschema.ValidationError: if the data does not conform to the schema
  :return: None
  :rtype: None
  """
  try:
    jsonschema.validate(instance=data, schema=schema)
    return data
  except jsonschema.ValidationError as e:
    print(f"Validation failed: {e.message}")


START = datetime(2025, 6, 1, 0, 0)
END = datetime(2025, 6, 30, 0, 0)


class AlpacaAvailablePairs(Enum):
  """
  Enum for available trading pairs on Alpaca.
  Currently includes BTC/USD and TSLA/USD.
  """

  BTCUSD = "BTC/USD"
  TSLAUSD = "TSLA/USD"  # assuming alpaca is usede


class TimeFrame(Enum):
  """
  Enum for time frames.
  Currently includes 1 Day and 1 Month.
  """

  ONEDAY = "1D"
  ONEHOUR = "1H"
  FIVEMINUTES = "5M"
  FIFTEENMINUTES = "15M"
  ONEMINUTE = "1M"
  FOURHOURS = "4H"


class Endpoint(Enum):
  """Enum for API endpoints.
  Currently includes one endpoint for Alpaca.
  """

  ALPACAEP0 = "https://data.alpaca.markets/v1beta3/crypto/us/bars?"  # endpoint 0


class Data:
  """Class to fetch data from remote or local file.
  :param symbol: trading pair, e.g., BTC/USD
  :param timeFrame: time frame for the data, e.g., 1D, 1M
  :param start: start datetime for the data
  :param end: end datetime for the data
  :param limit: maximum number of data points to fetch
  :param endpoint: API endpoint to fetch data from
  :param fetchedFromRemote: whether to fetch data from remote or local file
  :type symbol: AlpacaAvailablePairs
  :type timeFrame: TimeFrame
  :type start: datetime
  :type end: datetime
  :type limit: int
  :type endpoint: Endpoint
  :type fetchedFromRemote: bool
  :raises SystemExit: if there is an HTTP error during data fetching
  :return: None
  :rtype: None
  """

  def __init__(
    self,
    symbol: AlpacaAvailablePairs,
    timeFrame: TimeFrame,
    start: datetime = START,
    end: datetime = END,
    limit: int = 1000,
    endpoint: Endpoint = Endpoint.ALPACAEP0,
    fetchedFromRemote: bool = True,
  ):
    """Constructor for Data class.
    Initializes the Data object with the given parameters.
    :param symbol: trading pair, e.g., BTC/USD
    :param timeFrame: time frame for the data, e.g., 1D, 1M
    :param start: start datetime for the data
    :param end: end datetime for the data
    :param limit: maximum number of data points to fetch
    :param endpoint: API endpoint to fetch data from
    :param fetchedFromRemote: whether to fetch data from remote or local file
    :type symbol: AlpacaAvailablePairs
    :type timeFrame: TimeFrame
    :type start: datetime
    :type end: datetime
    :type limit: int
    :type endpoint: Endpoint
    :type fetchedFromRemote: bool
    :return: None
    :rtype: None
    """
    self.symbol = symbol
    self.timeFrame = timeFrame
    self.ep = endpoint
    self.limit = limit
    self.fetchedFromRemote = fetchedFromRemote
    self.start = start
    self.end = end
    self.length = 0

  # self.fetchFromRemote();  could be defaultly executed..

  def buildUrl(self):
    """
    Build the URL for fetching data from the API endpoint.
    :return: URL string with query parameters
    :rtype: str
    :raises: None
    """
    url = self.ep.value
    start = self.start.strftime("%Y-%m-%d")
    end = self.end.strftime("%Y-%m-%d")
    params = {
      "limit": str(self.limit),
      "timeframe": self.timeFrame.value,
      "symbols": self.symbol.value,
      "start": start,
      "end": end,
    }  # RFC-3339
    url += urllib.parse.urlencode(params)
    return url

  def fetchFromRemote(self):
    """
    Fetch data from the remote API endpoint.
    :return: HTTP status code of the response
    :rtype: int
    :raises SystemExit: if there is an HTTP error during data fetching
    """
    if not self.fetchedFromRemote:
      raise "resource should be fetched from file.. pls think about this."
    url = self.buildUrl()
    try:
      r = requests.get(url)  # will be the data parsed into json
      r.raise_for_status()
      self.data = r.json()["bars"]["BTC/USD"]  # defaultly take those values
      self.length = len(self.data)
      print(self.data)
      return r.status_code
    except requests.exceptions.HTTPError as err:
      raise SystemExit(err)

  def getDataLength(self):
    """
    Get the length of the fetched data.
    :return: length of the data
    :rtype: int
    """
    return self.length

  def getFromFile(self):
    """
    Fetch data from a local file.
    :return: None
    :rtype: None
    :raises: NotImplementedError
    """
    pass

  pass
